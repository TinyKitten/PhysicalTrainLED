from machine import Pin, SPI
import framebuf
import time
import network
import urequests
import time

DC = 8
RST = 12
MOSI = 11
SCK = 10
CS = 9


class StationDisplay(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 32

        self.cs = Pin(CS, Pin.OUT)
        self.rst = Pin(RST, Pin.OUT)

        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1, 1000_000)
        self.spi = SPI(
            1, 10000_000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=None
        )
        self.dc = Pin(DC, Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

        self.WHITE = 0xFFFF
        self.BLACK = 0x0000

    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """Initialize dispaly"""
        self.rst(1)
        time.sleep(0.001)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)

        self.write_cmd(0xAE)  # turn off OLED display*/

        self.write_cmd(0x04)  # turn off OLED display*/

        self.write_cmd(0x10)  # turn off OLED display*/

        self.write_cmd(0x40)  # set lower column address*/
        self.write_cmd(0x81)  # set higher column address*/
        self.write_cmd(
            0x80
        )  # --set start line address  Set Mapping RAM Display Start Line (0x00~0x3F, SSD1305_CMD)
        self.write_cmd(0xA1)  # --set contrast control register
        self.write_cmd(0xA6)  # Set SEG Output Current Brightness
        self.write_cmd(0xA8)  # --Set SEG/Column Mapping
        self.write_cmd(0x1F)  # Set COM/Row Scan Direction
        self.write_cmd(0xC8)  # --set normal display
        self.write_cmd(0xD3)  # --set multiplex ratio(1 to 64)
        self.write_cmd(0x00)  # --1/64 duty
        self.write_cmd(
            0xD5
        )  # -set display offset	Shift Mapping RAM Counter (0x00~0x3F)
        self.write_cmd(0xF0)  # -not offset
        self.write_cmd(0xD8)  # --set display clock divide ratio/oscillator frequency
        self.write_cmd(0x05)  # --set divide ratio, Set Clock as 100 Frames/Sec
        self.write_cmd(0xD9)  # --set pre-charge period
        self.write_cmd(0xC2)  # Set Pre-Charge as 15 Clocks & Discharge as 1 Clock
        self.write_cmd(0xDA)  # --set com pins hardware configuration
        self.write_cmd(0x12)
        self.write_cmd(0xDB)  # set vcomh
        self.write_cmd(0x08)  # Set VCOM Deselect Level
        self.write_cmd(0xAF)
        # -Set Page Addressing Mode (0x00/0x01/0x02)

    def show(self):
        for page in range(0, 4):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x04)
            self.write_cmd(0x10)
            self.dc(1)
            for num in range(0, 128):
                self.write_data(self.buffer[page * 128 + num])

    def get_is_connected(self):
        wlan = network.WLAN(network.STA_IF)
        return wlan.isconnected()

    def get_thinner_url(self, latitude, longitude):
        return "https://thinner-np6xgsb5la-an.a.run.app/nearby?latitude={}&longitude={}&en=true".format(
            latitude, longitude
        )


if __name__ == "__main__":
    WIFI_RETRY_COUNT = 0
    WIFI_MAXIMUM_RETRY = 10
    WIFI_CONNECTED = False

    SD = StationDisplay()

    SD.text("WELCOME!", 0, 8, SD.WHITE)
    SD.text("Please wait", 0, 18, SD.WHITE)
    SD.show()

    while WIFI_RETRY_COUNT <= WIFI_MAXIMUM_RETRY:
        WIFI_RETRY_COUNT += 1
        if SD.get_is_connected():
            WIFI_CONNECTED = True
            pass
        elif WIFI_RETRY_COUNT > WIFI_MAXIMUM_RETRY:
            SD.fill(0x0000)
            SD.text("WIFI ERROR!", 0, 8, SD.WHITE)
            SD.show()
            pass
        time.sleep(1)

    if WIFI_CONNECTED:
        SCROLL_X_PADDING = 40
        LATITUDE = 35.65887100
        LONGITUDE = 139.7012380

        sapi_res = urequests.get(SD.get_thinner_url(LATITUDE, LONGITUDE))

        text_array = sapi_res.text.split("\n")
        station_name = text_array[0].replace("Ō", "O").replace("ō", "o")
        transfer_lines = text_array[1]

        SD.fill(0x0000)
        SD.text(station_name, SCROLL_X_PADDING, 8, SD.WHITE)
        SD.text(transfer_lines, SCROLL_X_PADDING, 18, SD.WHITE)
        SD.rect(0, 0, SCROLL_X_PADDING, SD.height, SD.BLACK, True)
        SD.text(" NOW:", 0, 8, SD.WHITE)
        SD.text("LINE:", 0, 18, SD.WHITE)
        SD.show()

        wlan = network.WLAN(network.STA_IF)
        wlan.deinit()

        time.sleep(1)

        SPEED_FACTOR = 2
        line_x = SCROLL_X_PADDING / SPEED_FACTOR

        while True:
            SD.fill(0x0000)
            SD.text(station_name, SCROLL_X_PADDING, 8, SD.WHITE)
            SD.text(transfer_lines, int(line_x) * SPEED_FACTOR, 18, SD.WHITE)
            SD.rect(0, 0, SCROLL_X_PADDING, SD.height, SD.BLACK, True)
            SD.text(" NOW:", 0, 8, SD.WHITE)
            SD.text("LINE:", 0, 18, SD.WHITE)
            SD.show()

            line_x -= 1
            if line_x < -(len(transfer_lines) * 4):
                line_x = SD.width - SCROLL_X_PADDING

            time.sleep(0.01)
