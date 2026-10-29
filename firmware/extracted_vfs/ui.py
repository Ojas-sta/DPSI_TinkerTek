import lvgl as lv
from machine import unique_id,reset
import ubinascii,json,os
from esp32 import NVS
import esp_audio
import version
class DeviceState:
    def __init__(self):
        self.wifi = False
        self.wifi_flag = False

        self.server = False
        self.server_flag = False

        self.power = False
        self.power_num = 0
        self.power_num_flag = False
        self.power_flag = False
        self.lowpower_flag = False
        self.lowpower = False
        self.lowpower_num = 0
        self.charging = False
        self.charging_flag = False

        self.code = None
        self.code_flag = False
state = DeviceState()


# =========================
# 状态栏（绑定state）
# =========================
class StatusBar:
    def __init__(self):
        self.icons = {}
        self.power_bars = []
    def create(self, parent):
        # 背景图
        self.status = lv.image(parent)
        self.status.set_src("S:/UI/ti.bin")
        self.status.set_pos(0, 0)

        version_text = lv.label(self.status)
        version_text.set_pos(74, 9)
        version_text.set_text("V"+version.version)
        version_text.set_style_pad_all(0, lv.PART.MAIN)
        version_text.set_style_text_font(lv.font_montserrat_10, lv.PART.MAIN)
        version_text.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
        version_text.set_style_text_opa(lv.OPA.COVER, lv.PART.MAIN)
        # 图标
        self.icons["wifi"] = self._icon(parent, 223, 6)
        self.icons["server"] = self._icon(parent, 253, 6)
        self.icons["power"] = self._icon(parent, 280, 6)
        self.icons["charge"] = self._icon(parent, 307, 8)
        self.icons["charge"].set_src("S:/UI/charging.png")
        self.icons["charge"].add_flag(lv.obj.FLAG.HIDDEN)
        self.icons["wifi"].set_src("S:/UI/wifi_off.png")
        self.icons["server"].set_src("S:/UI/sever_off.png")
        self.icons["power"].set_src("S:/UI/no_power.png")

        self.icons["power_label"] = lv.obj(self.icons["power"])
        self.create_power_bars(self.icons["power_label"],4)
        self.icons["power_label"].set_size(20,10)
        self.icons["power_label"].set_pos(2, 1)
        self.icons["power_label"].set_style_pad_all(0, 0)
        self.icons["power_label"].set_style_radius(0, 0)
        self.icons["power_label"].set_style_border_width(0, 0)
        self.icons["power_label"].set_style_bg_opa(0, 0)
        self.icons["power_label"].add_flag(lv.obj.FLAG.HIDDEN)

    def create_power_bars(self, parent, num):
        self.power_bars = []

        for i in range(num):
            bar = lv.obj(parent)
            bar.remove_style_all()

            bar.set_size(3, 9)
            bar.set_pos(1 + i * 5, 1)

            bar.set_style_bg_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
            bar.set_style_bg_opa(255, lv.PART.MAIN)
            bar.set_style_radius(0, lv.PART.MAIN)

            self.power_bars.append(bar)
    def set_power(self, level):
        # level: 0~4
        for i, bar in enumerate(self.power_bars):
            if i < level:
                bar.set_style_bg_opa(255, lv.PART.MAIN)  # 亮
            else:
                bar.set_style_bg_opa(0, lv.PART.MAIN)   # 暗（或隐藏）
    def _icon(self, parent, x, y):
        im = lv.image(parent)
        im.set_pos(x, y)
        return im
status = StatusBar()

class Page:
    def __init__(self):
        self.page1 = None
        self.page2 = None

    def left_click(self,e):
        self.show_page(1)

    def right_click(self,e):
        self.show_page(2)

    def show_page(self,idx):
        if idx == 1:
            self.page1.remove_flag(lv.obj.FLAG.HIDDEN)
            self.page2.add_flag(lv.obj.FLAG.HIDDEN)
        else:
            self.page1.add_flag(lv.obj.FLAG.HIDDEN)
            self.page2.remove_flag(lv.obj.FLAG.HIDDEN)
        try:
            lv.refr_now(None)
        except Exception:
            pass

    def _make_top_buttons(self,parent,num,left_cb=None, right_cb=None, left_img=None, right_img=None):
        top = lv.obj(parent)
        top.set_size(320, 40)
        top.set_pos(0, 0)

        top.set_style_border_width(0, 0)
        top.set_style_radius(0, 0)
        top.set_style_bg_color(lv.color_hex(0x3E3A39), 0)
        top.set_style_bg_opa(255, 0)
        top.set_style_pad_all(0, 0)
        if num == 1:
            # 左按钮
            btn_l = lv.button(top)
            btn_l.set_size(155, 33)
            btn_l.set_pos(4, 4)
            btn_l.set_style_bg_color(lv.color_hex(0x72DFD8), 0)
            btn_l.set_style_radius(5, 0)
            btn_l.set_style_bg_opa(255, 0)
            btn_l.set_style_pad_all(0, lv.PART.MAIN)
            btn_l.set_style_border_width(0, 0)

            btn_l_lable = lv.label(btn_l)
            btn_l_lable.set_size(90, 16)
            btn_l_lable.set_pos(52,9)
            btn_l_lable.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
            btn_l_lable.set_style_bg_opa(0, 0)
            btn_l_lable.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
            btn_l_lable.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
            btn_l_lable.set_text("App  List")
        
            # 右按钮
            btn_r = lv.button(top)
            btn_r.set_size(155, 33)
            btn_r.set_pos(161, 4)
            btn_r.set_style_border_width(1, 0)
            btn_r.set_style_radius(5, 0)
            btn_r.set_style_border_color(lv.color_hex(0x72DFD8), 0)
            btn_r.set_style_bg_opa(0, 0)
            btn_r.set_style_pad_all(0, 0)

            btn_r_lable = lv.label(btn_r)
            btn_r_lable.set_size(100, 16)
            btn_r_lable.set_pos(47,9)
            btn_r_lable.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
            btn_r_lable.set_style_bg_opa(0, 0)
            btn_r_lable.set_style_text_color(lv.color_hex(0x72DFD8), lv.PART.MAIN)
            btn_r_lable.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
            btn_r_lable.set_text("Conn. Status")
        else:
            # 左按钮
            btn_l = lv.button(top)
            btn_l.set_size(155, 33)
            btn_l.set_pos(4, 4)
            btn_l.set_style_border_width(1, 0)
            btn_l.set_style_radius(5, 0)
            btn_l.set_style_border_color(lv.color_hex(0x72DFD8), 0)
            btn_l.set_style_bg_opa(0, 0)
            btn_l.set_style_pad_all(0, 0)

            btn_l_lable = lv.label(btn_l)
            btn_l_lable.set_size(90, 16)
            btn_l_lable.set_pos(52,9)
            btn_l_lable.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
            btn_l_lable.set_style_bg_opa(0, 0)
            btn_l_lable.set_style_text_color(lv.color_hex(0x72DFD8), lv.PART.MAIN)
            btn_l_lable.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
            btn_l_lable.set_text("App  List")
            # 右按钮
            btn_r = lv.button(top)
            btn_r.set_size(155, 33)
            btn_r.set_pos(161, 4)
            btn_r.set_style_bg_color(lv.color_hex(0x72DFD8), 0)
            btn_r.set_style_radius(5, 0)
            btn_r.set_style_bg_opa(255, 0)
            btn_r.set_style_pad_all(0, lv.PART.MAIN)
            btn_r.set_style_border_width(0, 0)

            btn_r_lable = lv.label(btn_r)
            btn_r_lable.set_size(100, 16)
            btn_r_lable.set_pos(47,9)
            btn_r_lable.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
            btn_r_lable.set_style_bg_opa(0, 0)
            btn_r_lable.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
            btn_r_lable.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
            btn_r_lable.set_text("Conn. Status")
        if left_img:
            iml = lv.image(btn_l)
            iml.set_src(left_img)
            iml.set_pos(30, 6)

        if left_cb:
            btn_l.add_event_cb(lambda e: left_cb(e), lv.EVENT.PRESSED, None)

        if right_img:
            imr = lv.image(btn_r)
            imr.set_src(right_img)
            imr.set_pos(25, 7)

        if right_cb:
            btn_r.add_event_cb(lambda e: right_cb(e), lv.EVENT.PRESSED, None)

        return top

    def create_page1(self, parent):
        self.page1 = lv.obj(parent)
        self.page1.set_size(320, 214)
        self.page1.set_pos(0, 0)
        self.page1.set_style_border_width(0, 0)
        self.page1.set_style_radius(0, 0)
        self.page1.set_style_pad_all(0, 0)

        self._make_top_buttons(
            self.page1,1,
            left_cb=None,
            right_cb=self.right_click,
            left_img="S:/UI/app_cl.bin",
            right_img="S:/UI/conn_un.bin"
        )
        page1_area = lv.obj(self.page1)
        page1_area.set_size(320, 174)
        page1_area.set_pos(0, 40)
        page1_area.set_style_border_width(0, 0)
        page1_area.set_style_radius(0, 0)
        page1_area.set_style_bg_opa(255, 0)
        page1_area.set_style_pad_all(0, 0)
        page1_area.set_style_bg_color(lv.color_hex(0x4C4C4D), 0)

        list_area = lv.obj(page1_area)
        list_area.set_size(247, 169)
        list_area.set_pos(4, 2)
        list_area.set_style_bg_opa(0, 0)
        list_area.set_style_border_width(2, 0)
        list_area.set_style_border_color(lv.color_hex(0x84909C), 0)
        list_area.set_style_pad_all(0, 0)
        list_area.set_style_radius(4, 0)

        list_title = lv.obj(list_area)
        list_title.set_size(243, 20)
        list_title.set_pos(0, 0)
        list_title.set_style_border_width(0, 0)
        list_title.set_style_bg_color(lv.color_hex(0x64696F), 0)
        list_title.set_style_bg_opa(255, 0)
        list_title.set_style_pad_all(0, 0)
        list_title.set_style_radius(0, 0)

        list_title_text = lv.label(list_title)
        list_title_text.set_pos(2, 1)
        list_title_text.set_text("PROGRAM  LIST")
        list_title_text.set_style_pad_all(0, lv.PART.MAIN)
        list_title_text.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        list_title_text.set_style_text_color(lv.color_hex(0x72DFD8), lv.PART.MAIN)
        list_title_text.set_style_text_opa(lv.OPA.COVER, lv.PART.MAIN)
        files = []
        try:
            with open("program/program.txt", "r") as f:
                for line in f.readlines():
                    name = line.strip()
                    files.append(name)
        except:
            files = []

        files = files[:6]   # 最多6个
        while len(files) < 6:
            files.append("")
        file_num = len(files)
        rows = []
        selected_index = 0

        for i in range(6):
            # --- row ---
            row = lv.obj(list_area)
            row.set_size(240, 21)
            row.set_pos(0, 24 + i * 24)
            row.set_style_radius(0, 0)
            row.set_style_border_width(0, 0)
            row.set_style_bg_opa(0, 0)
            row.set_style_pad_all(0, 0)

            # --- index ---
            num = lv.label(row)
            num.set_size(24, 21)
            num.set_pos(0, 0)
            num.set_style_border_width(2, 0)
            num.set_style_bg_color(lv.color_hex(0x4C4C4D), 0)
            num.set_style_radius(5, 0)
            num.set_style_bg_opa(255, 0)
            num.set_style_border_color(lv.color_hex(0x868687), 0)
            num.set_style_pad_all(0, lv.PART.MAIN)
            num.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
            num.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
            num.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)

            name = lv.label(row)
            name.set_size(210, 21)
            name.set_pos(28, 0)
            name.set_style_border_width(2, 0)
            name.set_style_bg_color(lv.color_hex(0x4C4C4D), 0)
            name.set_style_bg_opa(255, 0)
            name.set_style_radius(5, 0)
            name.set_style_border_color(lv.color_hex(0x868687), 0)
            name.set_style_pad_all(0, lv.PART.MAIN)
            name.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
            name.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
            num.set_text(f"{i+1}.")
            if files[i]:
                name.set_text("  " + files[i])
            else:
                name.set_text("")
            if file_num > 0:
                if i == selected_index:
                    num.set_style_border_color(lv.color_hex(0x72DFD8), 0)
                    num.set_style_bg_color(lv.color_hex(0x72DFD8), 0)
                    name.set_style_border_color(lv.color_hex(0x72DFD8), 0)
                    name.set_style_bg_color(lv.color_hex(0x72DFD8), 0)
            rows.append((row, num,name))
        def select_index(select_num):
            for i in range(file_num):
                row, num, name = rows[i] 
                if i == select_num:
                    num.set_style_border_color(lv.color_hex(0x72DFD8), 0)
                    num.set_style_bg_color(lv.color_hex(0x72DFD8), 0)
                    name.set_style_border_color(lv.color_hex(0x72DFD8), 0)
                    name.set_style_bg_color(lv.color_hex(0x72DFD8), 0)               
                else:  
                    num.set_style_border_color(lv.color_hex(0x868687), 0)
                    num.set_style_bg_color(lv.color_hex(0x4C4C4D), 0)
                    name.set_style_border_color(lv.color_hex(0x868687), 0)
                    name.set_style_bg_color(lv.color_hex(0x4C4C4D), 0)
                            
        def up_click(e):
            nonlocal selected_index,file_num
            selected_index = selected_index - 1
            if selected_index < 0:
                selected_index = file_num-1
            select_index(selected_index)

        def down_click(e):
            nonlocal selected_index,file_num
            selected_index = selected_index + 1
            if selected_index > file_num-1:
                selected_index = 0
            select_index(selected_index)
        def run_click(e):
            nonlocal selected_index,files,file_num
            if file_num > 0:
                with open("program/"+files[selected_index], "r") as f:
                    code = f.read()
                with open("py/user_code.py", "w") as f:
                    f.write(code)
                nvs = NVS("mode")
                nvs.set_i32("opt", 1)
                nvs.commit()
                reset()
        up_panel = lv.button(page1_area)
        up_panel.set_size(55, 52)
        up_panel.set_pos(260, 2)
        up_panel.set_style_border_width(0, lv.PART.MAIN)
        up_panel.set_style_pad_all(0,lv.PART.MAIN)
        up_panel.set_style_bg_color(lv.color_hex(0x757576), 0)
        up_panel.set_style_radius(3, 0)

        up_image = lv.image(up_panel)
        up_image.set_src(lv.SYMBOL.UP)
        up_image.align(lv.ALIGN.CENTER, 0, 0)
        up_panel.add_event_cb(lambda e: up_click(e), lv.EVENT.PRESSED, None)

        down_panel = lv.button(page1_area)
        down_panel.set_size(55, 52)
        down_panel.set_pos(260, 58)
        down_panel.set_style_border_width(0, lv.PART.MAIN)
        down_panel.set_style_pad_all(0,lv.PART.MAIN)
        down_panel.set_style_bg_color(lv.color_hex(0x757576), 0)
        down_panel.set_style_radius(3, 0)

        down_image = lv.image(down_panel)
        down_image.set_src(lv.SYMBOL.DOWN)
        down_image.align(lv.ALIGN.CENTER, 0, 0)
        down_panel.add_event_cb(lambda e: down_click(e), lv.EVENT.PRESSED, None)

        run_panel = lv.button(page1_area)
        run_panel.set_size(55, 56)
        run_panel.set_pos(260, 115)
        run_panel.set_style_border_width(0, lv.PART.MAIN)
        run_panel.set_style_pad_all(0,lv.PART.MAIN)
        run_panel.set_style_bg_color(lv.color_hex(0xAB75EE), 0)
        run_panel.set_style_radius(3, 0)

        run_lable = lv.label(run_panel)
        run_lable.set_size(55, 16)
        run_lable.set_pos(0, 22)
        run_lable.set_style_text_align(lv.TEXT_ALIGN.CENTER, lv.PART.MAIN)
        run_lable.set_style_bg_opa(0, 0)
        run_lable.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
        run_lable.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        run_lable.set_text("RUN")
        run_panel.add_event_cb(lambda e: run_click(e), lv.EVENT.PRESSED, None)
    def create_page2(self, parent):
        self.page2 = lv.obj(parent)
        self.page2.set_size(320, 214)
        self.page2.set_pos(0, 0)
        self.page2.set_style_border_width(0, 0)
        self.page2.set_style_radius(0, 0)
        self.page2.set_style_pad_all(0, 0)
        self.page2.add_flag(lv.obj.FLAG.HIDDEN)

        self._make_top_buttons(
            self.page2,2,
            left_cb=self.left_click,
            right_cb=None,
            left_img="S:/UI/app_un.bin",
            right_img="S:/UI/conn_cl.bin"
        )
        page2_area = lv.obj(self.page2)
        page2_area.set_size(320, 174)
        page2_area.set_pos(0, 40)
        page2_area.set_style_border_width(0, 0)
        page2_area.set_style_radius(0, 0)
        page2_area.set_style_bg_opa(255, 0)
        page2_area.set_style_pad_all(0, 0)

        set_area = lv.obj(page2_area)
        set_area.set_size(312, 169)
        set_area.set_pos(4, 2)
        set_area.set_style_border_width(0, 0)
        set_area.set_style_pad_all(0, 0)

        wifi_panel = lv.obj(set_area)
        wifi_panel.set_size(156, 169)
        wifi_panel.set_pos(0, 0)
        wifi_panel.set_style_border_width(0, 0)
        wifi_panel.set_style_bg_color(lv.color_hex(0x3E3A39), 0)
        wifi_panel.set_style_bg_opa(255, 0)
        wifi_panel.set_style_pad_all(0, 0)

        wifi_title = lv.obj(wifi_panel)
        wifi_title.set_size(156, 26)
        wifi_title.set_pos(0, 0)
        wifi_title.set_style_border_width(0, 0)
        wifi_title.set_style_bg_color(lv.color_hex(0x72DFD8), 0)
        wifi_title.set_style_bg_opa(255, 0)
        wifi_title.set_style_pad_all(0, 0)
        wifi_title.set_style_radius(0, 0)

        wifi_title_text = lv.label(wifi_title)
        wifi_title_text.set_text("WIFI")
        wifi_title_text.center()
        wifi_title_text.set_style_pad_all(0, lv.PART.MAIN)
        wifi_title_text.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        wifi_title_text.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
        wifi_title_text.set_style_text_opa(lv.OPA.COVER, lv.PART.MAIN)
        wifi_title_text.set_style_text_letter_space(1, 0)

        ssid_text = lv.label(wifi_panel)
        ssid_text.set_size(100,15)
        ssid_text.set_pos(10, 36)
        ssid_text.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        ssid_text.set_style_bg_opa(0, 0)
        ssid_text.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        ssid_text.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
        ssid_text.set_text("SSID:")

        ssid_panel = lv.obj(wifi_panel)
        ssid_panel.set_size(136, 26)
        ssid_panel.set_pos(10, 56)
        ssid_panel.set_style_border_width(0, lv.PART.MAIN)
        ssid_panel.set_style_pad_all(0,lv.PART.MAIN)
        ssid_panel.set_style_bg_color(lv.color_hex(0x595655), 0)
        ssid_panel.set_style_radius(5, 0)

        try:
            with open("config.txt", "r") as f:
                cfg = json.loads(f.read())
                wifi_cfg = cfg.get("wifi", {}) if isinstance(cfg, dict) else {}
                ssid = wifi_cfg.get("ssid")
                pwd = wifi_cfg.get("pswd")
        except Exception as e:
            ssid = ''
            pwd = ''
        ssid_lable = lv.label(ssid_panel)
        ssid_lable.set_size(130, 16)
        ssid_lable.set_pos(3, 4)
        ssid_lable.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        ssid_lable.set_style_bg_opa(0, 0)
        ssid_lable.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
        ssid_lable.set_style_text_font(lv.font_montserrat_14, lv.PART.MAIN)
        ssid_lable.set_text(ssid)

        pass_text = lv.label(wifi_panel)
        pass_text.set_size(100,15)
        pass_text.set_pos(10,100)
        pass_text.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        pass_text.set_style_bg_opa(0, 0)
        pass_text.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        pass_text.set_style_text_color(lv.color_hex(0xFFFFFF), lv.PART.MAIN)
        pass_text.set_text("PASS:")

        pass_panel = lv.obj(wifi_panel)
        pass_panel.set_size(136, 26)
        pass_panel.set_pos(10, 120)
        pass_panel.set_style_border_width(0, lv.PART.MAIN)
        pass_panel.set_style_pad_all(0,lv.PART.MAIN)
        pass_panel.set_style_bg_color(lv.color_hex(0x595655), 0)
        pass_panel.set_style_radius(5, 0)

        psss_lable = lv.label(pass_panel)
        psss_lable.set_size(130, 16)
        psss_lable.set_pos(3, 4)
        psss_lable.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        psss_lable.set_style_bg_opa(0, 0)
        psss_lable.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
        psss_lable.set_style_text_font(lv.font_montserrat_14, lv.PART.MAIN)
        psss_lable.set_text(pwd)

        wifi_bg1 =  lv.obj(wifi_title)
        wifi_bg1.set_size(10,10)
        wifi_bg1.set_pos(0, 0)
        wifi_bg1.set_style_border_width(0, 0)
        wifi_bg1.set_style_radius(0, 0)
        wifi_bg1.set_style_bg_opa(255, 0)
        wifi_bg1.set_style_pad_all(0, 0)

        wifi_bg2 =  lv.obj(wifi_title)
        wifi_bg2.set_size(20,20)
        wifi_bg2.set_pos(0, 0)
        wifi_bg2.set_style_bg_color(lv.color_hex(0x72DFD8), 0)
        wifi_bg2.set_style_border_width(0, 0)
        wifi_bg2.set_style_bg_opa(255, 0)
        wifi_bg2.set_style_pad_all(0, 0)

        wifi_bg3 =  lv.obj(wifi_panel)
        wifi_bg3.set_size(10,10)
        wifi_bg3.set_pos(146, 159)
        wifi_bg3.set_style_border_width(0, 0)
        wifi_bg3.set_style_bg_color(lv.color_hex(0x3E3A39), 0)
        wifi_bg3.set_style_radius(0, 0)
        wifi_bg3.set_style_bg_opa(255, 0)
        wifi_bg3.set_style_pad_all(0, 0)

        device_panel = lv.obj(set_area)
        device_panel.set_size(156, 169)
        device_panel.set_pos(156, 0)
        device_panel.set_style_border_width(0, 0)
        device_panel.set_style_bg_color(lv.color_hex(0x61656B), 0)
        device_panel.set_style_bg_opa(255, 0)
        device_panel.set_style_pad_all(0, 0)
        def parse_wav_header(wav_bytes):
            num_channels = int.from_bytes(wav_bytes[22:24], 'little')
            sample_rate = int.from_bytes(wav_bytes[24:28], 'little')
            bits_per_sample = int.from_bytes(wav_bytes[34:36], 'little')
            data_offset = 44
            return num_channels, sample_rate, bits_per_sample, data_offset
        def ip_click(e):
            esp_audio.music_vol_set(50)
            with open("music/clicked.wav", "rb") as f:
                header = f.read(44)
                channels, sample_rate, bits, offset = parse_wav_header(header)
                data = f.read()
            esp_audio.audio_config(sample_rate, bits, channels)
            esp_audio.audio_open()
            esp_audio.music_play(data)  # 发送音频数据进行播放
            esp_audio.audio_close()

        ip_panel = lv.button(device_panel)
        ip_panel.set_size(88,72)
        ip_panel.set_pos(68, 97)
        ip_panel.set_style_bg_opa(0, 0)
        ip_panel.set_style_pad_all(0, 0)
        ip_panel.add_event_cb(lambda e: ip_click(e), lv.EVENT.PRESSED, None)
        ip_img = lv.image(ip_panel)
        ip_img.set_src("S:/UI/IP.bin")

        device_title = lv.obj(device_panel)
        device_title.set_size(156, 26)
        device_title.set_pos(0, 0)
        device_title.set_style_border_width(0, 0)
        device_title.set_style_bg_color(lv.color_hex(0x757D87), 0)
        device_title.set_style_bg_opa(255, 0)
        device_title.set_style_pad_all(0, 0)
        device_title.set_style_radius(0, 0)
        
        device_title_text = lv.label(device_title)
        device_title_text.set_text("DEVICE  INFO")
        device_title_text.center()
        device_title_text.set_style_pad_all(0, lv.PART.MAIN)
        device_title_text.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        device_title_text.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
        device_title_text.set_style_text_opa(lv.OPA.COVER, lv.PART.MAIN)

        mac_text = lv.label(device_panel)
        mac_text.set_size(100,15)
        mac_text.set_pos(10, 33)
        mac_text.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        mac_text.set_style_bg_opa(0, 0)
        mac_text.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        mac_text.set_style_text_color(lv.color_hex(0x6CD4CE), lv.PART.MAIN)
        mac_text.set_text("MAC:")

        mac_lable = lv.label(device_panel)
        mac_lable.set_size(130, 16)
        mac_lable.set_pos(10, 53)
        mac_lable.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        mac_lable.set_style_bg_opa(0, 0)
        mac_lable.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
        mac_lable.set_style_text_font(lv.font_montserrat_14, lv.PART.MAIN)
        mac_lable.set_text(ubinascii.hexlify(unique_id()).decode().upper())

        code_text = lv.label(device_panel)
        code_text.set_size(140,20)
        code_text.set_pos(10,77)
        code_text.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        code_text.set_style_bg_opa(0, 0)
        code_text.set_style_text_font(lv.font_poppins_14, lv.PART.MAIN)
        code_text.set_style_text_color(lv.color_hex(0x6CD4CE), lv.PART.MAIN)
        code_text.set_text("Pairing  Code:")

        self.code_lable = lv.label(device_panel)
        self.code_lable.set_size(80, 20)
        self.code_lable.set_pos(10, 97)
        self.code_lable.set_style_text_align(lv.TEXT_ALIGN.LEFT, lv.PART.MAIN)
        self.code_lable.set_style_bg_opa(0, 0)
        self.code_lable.set_style_text_color(lv.color_hex(0xFEFFFF), lv.PART.MAIN)
        self.code_lable.set_style_text_font(lv.font_montserrat_14, lv.PART.MAIN)
        self.code_lable.set_text("")

        device_bg1 =  lv.obj(device_title)
        device_bg1.set_size(10,10)
        device_bg1.set_pos(146, 0)
        device_bg1.set_style_border_width(0, 0)
        device_bg1.set_style_radius(0, 0)
        device_bg1.set_style_bg_opa(255, 0)
        device_bg1.set_style_pad_all(0, 0)

        device_bg2 =  lv.obj(device_title)
        device_bg2.set_size(20,20)
        device_bg2.set_pos(136, 0)
        device_bg2.set_style_bg_color(lv.color_hex(0x757D87), 0)
        device_bg2.set_style_border_width(0, 0)
        device_bg2.set_style_bg_opa(255, 0)
        device_bg2.set_style_pad_all(0, 0)

        device_bg3 =  lv.obj(device_panel)
        device_bg3.set_size(10,10)
        device_bg3.set_pos(0, 159)
        device_bg3.set_style_border_width(0, 0)
        device_bg3.set_style_bg_color(lv.color_hex(0x61656B), 0)
        device_bg3.set_style_radius(0, 0)
        device_bg3.set_style_bg_opa(255, 0)
        device_bg3.set_style_pad_all(0, 0)
page=Page()

def refresh(timer=None):
    if state.wifi_flag:
        status.icons["wifi"].set_src(
            "S:/UI/wifi_on.png" if state.wifi else "S:/UI/wifi_off.png"
        )
        state.wifi_flag = False
    if state.server_flag:
        status.icons["server"].set_src(
            "S:/UI/sever_on.png" if state.server else "S:/UI/sever_off.png"
        )
        state.server_flag = False
    if state.power_flag:
        if state.power:
            status.icons["power"].set_src("S:/UI/power.png")
            status.icons["power_label"].remove_flag(lv.obj.FLAG.HIDDEN)
        else:
            state.lowpower_flag = False
            status.icons["power"].set_src("S:/UI/no_power.png")
            status.icons["power_label"].add_flag(lv.obj.FLAG.HIDDEN)
        state.power_flag = False
    if state.charging_flag:
        if state.charging:
            status.icons["charge"].remove_flag(lv.obj.FLAG.HIDDEN)
        else:
            status.icons["charge"].add_flag(lv.obj.FLAG.HIDDEN)
        state.charging_flag = False
    if state.code_flag:
        page.code_lable.set_text(state.code)
        state.code_flag = False
    if state.power_num_flag:
        if state.power_num == 100:
            status.set_power(4)
            state.lowpower_flag = False
        elif state.power_num == 75:
            status.set_power(3)
            state.lowpower_flag = False
        elif state.power_num == 50:
            status.set_power(2)
            state.lowpower_flag = False
        elif state.power_num == 25:
            status.set_power(1)
            state.lowpower_flag = False
        elif state.power_num == 0:
            status.set_power(0)
            state.lowpower_flag = True
        state.power_num_flag = False
    if state.lowpower_flag:
        if state.lowpower_num >3:
            state.lowpower_num =0
            state.lowpower = not state.lowpower
            if state.lowpower:
                status.icons["power"].add_flag(lv.obj.FLAG.HIDDEN)
            else:
                status.icons["power"].remove_flag(lv.obj.FLAG.HIDDEN)
        else:
            state.lowpower_num +=1
        

def init_ui():
    # =========================
    # 主屏
    # =========================
    scr = lv.screen_active()
    status.create(scr)

    # =========================
    # body 容器
    # =========================
    body = lv.obj(scr)
    body.set_size(320, 214)
    body.set_pos(0, 26)
    body.set_style_border_width(0, 0)
    body.set_style_radius(0, 0)
    body.set_style_pad_all(0, 0)
    
    page.create_page1(body)
    page.create_page2(body)

    page.show_page(2)
    try:
        lv.timer_create(refresh, 100, None)
    except Exception:
        # Fallback: if lv timer is unavailable, call once without thread.
        refresh()

