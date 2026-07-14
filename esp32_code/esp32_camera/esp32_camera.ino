#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"

// -------------------- WIFI --------------------
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";

// -------------------- MIDDLEWARE --------------------
const char* apiHost = "iot-middleware-production-4aa8.up.railway.app";
const int apiPort = 443;
const char* apiBasePath = "/api";

const char* cameraDeviceId = "ESP32_CAM_001";
const char* monitoredPirDeviceId = "ESP32_PIR_001";

const int defaultImagesPerEvent = 10;
const unsigned long pendingPollIntervalMs = 1000;
const unsigned long uploadHttpTimeoutMs = 45000;
const unsigned long postTimeoutResultWaitMs = 45000;
const unsigned long postTimeoutPollMs = 2000;
const unsigned long serverErrorFallbackWaitMs = 30000;

// -------------------- AI THINKER PINS --------------------
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27

#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22

struct CapturedImage {
	uint8_t* data;
	size_t len;
};

void connectWiFi() {
	if (WiFi.status() == WL_CONNECTED) {
		return;
	}

	Serial.printf("Connecting WiFi: %s\n", ssid);
	WiFi.mode(WIFI_STA);
	WiFi.begin(ssid, password);

	int attempts = 0;
	while (WiFi.status() != WL_CONNECTED && attempts < 40) {
		delay(500);
		Serial.print(".");
		attempts++;
	}
	Serial.println();

	if (WiFi.status() == WL_CONNECTED) {
		Serial.printf("WiFi OK. IP=%s RSSI=%d dBm\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
		return;
	}

	Serial.println("WiFi failed. Restarting in 5 seconds...");
	delay(5000);
	ESP.restart();
}

bool initCamera() {
	camera_config_t config;
	config.ledc_channel = LEDC_CHANNEL_0;
	config.ledc_timer = LEDC_TIMER_0;
	config.pin_d0 = Y2_GPIO_NUM;
	config.pin_d1 = Y3_GPIO_NUM;
	config.pin_d2 = Y4_GPIO_NUM;
	config.pin_d3 = Y5_GPIO_NUM;
	config.pin_d4 = Y6_GPIO_NUM;
	config.pin_d5 = Y7_GPIO_NUM;
	config.pin_d6 = Y8_GPIO_NUM;
	config.pin_d7 = Y9_GPIO_NUM;
	config.pin_xclk = XCLK_GPIO_NUM;
	config.pin_pclk = PCLK_GPIO_NUM;
	config.pin_vsync = VSYNC_GPIO_NUM;
	config.pin_href = HREF_GPIO_NUM;
	config.pin_sscb_sda = SIOD_GPIO_NUM;
	config.pin_sscb_scl = SIOC_GPIO_NUM;
	config.pin_pwdn = PWDN_GPIO_NUM;
	config.pin_reset = RESET_GPIO_NUM;
	config.xclk_freq_hz = 20000000;
	config.pixel_format = PIXFORMAT_JPEG;

	if (psramFound()) {
		config.frame_size = FRAMESIZE_QVGA;
		config.jpeg_quality = 14;
		config.fb_count = 2;
	} else {
		config.frame_size = FRAMESIZE_QQVGA;
		config.jpeg_quality = 16;
		config.fb_count = 1;
	}

	esp_err_t err = esp_camera_init(&config);
	if (err != ESP_OK) {
		Serial.printf("Camera init failed: 0x%x\n", err);
		return false;
	}

	sensor_t* sensor = esp_camera_sensor_get();
	if (sensor != nullptr) {
		sensor->set_brightness(sensor, 0);
		sensor->set_contrast(sensor, 0);
		sensor->set_saturation(sensor, 0);
	}

	Serial.println("Camera initialized.");
	return true;
}

bool getJson(const String& path, String& responseBody, int& httpCode) {
	if (WiFi.status() != WL_CONNECTED) {
		connectWiFi();
	}

	WiFiClientSecure client;
	client.setInsecure();

	HTTPClient http;
	String url = String("https://") + apiHost + path;
	if (!http.begin(client, url)) {
		Serial.println("HTTP begin failed (GET)");
		return false;
	}

	http.setTimeout(15000);
	httpCode = http.GET();
	responseBody = http.getString();
	http.end();

	return httpCode > 0;
}

bool getEventResultSignal(const String& eventId, String& signalOut, bool& isReady) {
	String response;
	int httpCode = -1;
	String path = String(apiBasePath) + "/pir/result/?event_id=" + eventId;

	if (!getJson(path, response, httpCode) || httpCode != 200) {
		isReady = false;
		return false;
	}

	StaticJsonDocument<768> res;
	DeserializationError err = deserializeJson(res, response);
	if (err) {
		isReady = false;
		return false;
	}

	const char* status = res["status"] | "pending";
	if (String(status) == "pending") {
		isReady = false;
		return true;
	}

	const char* signal = res["signal"] | "unknown";
	signalOut = String(signal);
	isReady = true;
	return true;
}

bool waitForReadyResult(const String& eventId, unsigned long waitMs, const char* reasonLabel) {
	Serial.printf("Waiting for result fallback (%s)...\n", reasonLabel);
	unsigned long startMs = millis();
	while (millis() - startMs < waitMs) {
		String signal;
		bool isReady = false;
		bool ok = getEventResultSignal(eventId, signal, isReady);
		if (ok && isReady) {
			Serial.printf("Fallback result detected: %s\n", signal.c_str());
			return true;
		}
		delay(postTimeoutPollMs);
	}
	return false;
}

void freeCapturedImages(CapturedImage* images, int count) {
	for (int i = 0; i < count; i++) {
		if (images[i].data != nullptr) {
			free(images[i].data);
			images[i].data = nullptr;
			images[i].len = 0;
		}
	}
}

int captureImages(CapturedImage* images, int targetCount) {
	int captured = 0;

	for (int i = 0; i < targetCount; i++) {
		camera_fb_t* fb = esp_camera_fb_get();
		if (!fb) {
			Serial.printf("Capture failed at %d/%d\n", i + 1, targetCount);
			delay(120);
			continue;
		}

		uint8_t* copyBuffer = (uint8_t*)ps_malloc(fb->len);
		if (copyBuffer == nullptr) {
			copyBuffer = (uint8_t*)malloc(fb->len);
		}

		if (copyBuffer == nullptr) {
			Serial.println("Out of memory while copying frame.");
			esp_camera_fb_return(fb);
			break;
		}

		memcpy(copyBuffer, fb->buf, fb->len);
		images[captured].data = copyBuffer;
		images[captured].len = fb->len;
		captured++;

		Serial.printf("Captured %d/%d (%u bytes)\n", captured, targetCount, (unsigned int)fb->len);
		esp_camera_fb_return(fb);
		delay(120);
	}

	return captured;
}

bool uploadImagesMultipart(const String& eventId, CapturedImage* images, int imageCount) {
	if (imageCount <= 0) {
		return false;
	}

	if (WiFi.status() != WL_CONNECTED) {
		connectWiFi();
	}

	const String boundary = "----ESP32Boundary7MA4YWxkTrZu0gW";

	String preEvent = "--" + boundary + "\r\n";
	preEvent += "Content-Disposition: form-data; name=\"event_id\"\r\n\r\n";
	preEvent += eventId + "\r\n";

	String preDevice = "--" + boundary + "\r\n";
	preDevice += "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n";
	preDevice += String(cameraDeviceId) + "\r\n";

	String closing = "--" + boundary + "--\r\n";

	size_t totalLen = preEvent.length() + preDevice.length() + closing.length();

	for (int i = 0; i < imageCount; i++) {
		String imageHeader = "--" + boundary + "\r\n";
		imageHeader += "Content-Disposition: form-data; name=\"images[]\"; filename=\"img_" + String(i + 1) + ".jpg\"\r\n";
		imageHeader += "Content-Type: image/jpeg\r\n\r\n";

		totalLen += imageHeader.length();
		totalLen += images[i].len;
		totalLen += 2;  // \r\n
	}

	uint8_t* body = (uint8_t*)ps_malloc(totalLen);
	if (body == nullptr) {
		body = (uint8_t*)malloc(totalLen);
	}

	if (body == nullptr) {
		Serial.println("Not enough memory to build multipart body.");
		return false;
	}

	size_t offset = 0;

	auto appendRaw = [&](const uint8_t* src, size_t len) {
		memcpy(body + offset, src, len);
		offset += len;
	};

	auto appendString = [&](const String& s) {
		appendRaw((const uint8_t*)s.c_str(), s.length());
	};

	appendString(preEvent);
	appendString(preDevice);

	for (int i = 0; i < imageCount; i++) {
		String imageHeader = "--" + boundary + "\r\n";
		imageHeader += "Content-Disposition: form-data; name=\"images[]\"; filename=\"img_" + String(i + 1) + ".jpg\"\r\n";
		imageHeader += "Content-Type: image/jpeg\r\n\r\n";

		appendString(imageHeader);
		appendRaw(images[i].data, images[i].len);
		appendString("\r\n");
	}

	appendString(closing);

	WiFiClientSecure client;
	client.setInsecure();

	HTTPClient http;
	String url = String("https://") + apiHost + String(apiBasePath) + "/images/upload/";
	if (!http.begin(client, url)) {
		Serial.println("HTTP begin failed (UPLOAD)");
		free(body);
		return false;
	}

	http.setTimeout(uploadHttpTimeoutMs);
	http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

	int httpCode = http.POST(body, offset);
	String response = http.getString();

	free(body);
	http.end();

	Serial.printf("Upload response code: %d\n", httpCode);
	if (response.length() > 0) {
		Serial.printf("Upload response body: %s\n", response.c_str());
	}

	if (httpCode <= 0) {
		if (httpCode == -11) {
			if (waitForReadyResult(eventId, postTimeoutResultWaitMs, "http-timeout")) {
				return true;
			}
		}
		return false;
	}

	if (httpCode >= 500) {
		if (waitForReadyResult(eventId, serverErrorFallbackWaitMs, "server-error")) {
			return true;
		}
		return false;
	}

	if (httpCode != 200) {
		return false;
	}

	StaticJsonDocument<1024> res;
	DeserializationError err = deserializeJson(res, response);
	if (err) {
		Serial.printf("Upload JSON parse error: %s\n", err.c_str());
		return false;
	}

	bool success = res["success"] | false;
	const char* signal = res["pir_signal"] | "unknown";
	Serial.printf("Upload success=%s pir_signal=%s\n", success ? "true" : "false", signal);

	if (!success) {
		if (waitForReadyResult(eventId, serverErrorFallbackWaitMs, "api-success-false")) {
			return true;
		}
	}

	return success;
}

bool pollPendingEvent(String& eventIdOut, int& imagesToCaptureOut) {
	String response;
	int httpCode = -1;
	String path = String(apiBasePath) + "/pir/pending/?device_id=" + monitoredPirDeviceId;

	if (!getJson(path, response, httpCode)) {
		return false;
	}

	if (httpCode != 200) {
		return false;
	}

	StaticJsonDocument<768> res;
	DeserializationError err = deserializeJson(res, response);
	if (err) {
		Serial.printf("Pending JSON parse error: %s\n", err.c_str());
		return false;
	}

	bool hasEvent = res["has_event"] | false;
	if (!hasEvent) {
		return false;
	}

	const char* eventId = res["event_id"] | "";
	int imagesToCapture = res["images_to_capture"] | defaultImagesPerEvent;

	if (strlen(eventId) == 0) {
		return false;
	}

	eventIdOut = String(eventId);
	imagesToCaptureOut = imagesToCapture;
	return true;
}

void setup() {
	Serial.begin(115200);
	delay(300);

	Serial.println();
	Serial.println("==================================================");
	Serial.println("ESP32-CAM AI Thinker - Middleware Polling Camera");
	Serial.println("==================================================");

	connectWiFi();

	if (!initCamera()) {
		Serial.println("Camera init failed permanently. Restarting...");
		delay(3000);
		ESP.restart();
	}

	Serial.println("System ready.");
}

void loop() {
	if (WiFi.status() != WL_CONNECTED) {
		connectWiFi();
	}

	String eventId;
	int imagesToCapture = defaultImagesPerEvent;

	if (pollPendingEvent(eventId, imagesToCapture)) {
		if (imagesToCapture <= 0) {
			imagesToCapture = defaultImagesPerEvent;
		}

		if (imagesToCapture > 10) {
			imagesToCapture = 10;
		}

		Serial.printf("Pending event received: %s\n", eventId.c_str());
		Serial.printf("Target images: %d\n", imagesToCapture);

		CapturedImage images[10];
		for (int i = 0; i < 10; i++) {
			images[i].data = nullptr;
			images[i].len = 0;
		}

		int captured = captureImages(images, imagesToCapture);
		if (captured <= 0) {
			Serial.println("No images captured. Skipping upload.");
			freeCapturedImages(images, 10);
			delay(500);
			return;
		}

		bool uploaded = uploadImagesMultipart(eventId, images, captured);
		freeCapturedImages(images, 10);

		if (!uploaded) {
			Serial.println("Upload failed. Retrying once with fresh captures...");

			CapturedImage retryImages[10];
			for (int i = 0; i < 10; i++) {
				retryImages[i].data = nullptr;
				retryImages[i].len = 0;
			}

			int retryCaptured = captureImages(retryImages, imagesToCapture);
			if (retryCaptured > 0) {
				uploaded = uploadImagesMultipart(eventId, retryImages, retryCaptured);
			}
			freeCapturedImages(retryImages, 10);

			if (!uploaded) {
				Serial.println("Upload failed for this event after retry.");
			} else {
				Serial.println("Upload completed on retry.");
			}
		} else {
			Serial.println("Upload completed.");
		}
	}

	delay(pendingPollIntervalMs);
}
