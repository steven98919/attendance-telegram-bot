class Template_excel:

    header_text_blue = ['NAMA KARYAWAN','DIVISI','JABATAN']
    header_text_orange = ['HARI KERJA',"KEHADIRAN (HURUF A)","DINAS (Huruf DN)","KETERLAMBATAN (Huruf T)","SAKIT (Huruf S)","CUTI (Huruf C)","CUTI KHUSUS (Huruf K)","SETENGAH HARI (Huruf HD)"]

    header_text_alphabet = [chr(i) for i in range(ord('A'), ord('I') + 1)]

    common_properties = {
        "align": "center",
        "valign": "vcenter",
        "font_color": "black",
        'font_size': 11,
        'font_name': "Calibri",
        'border': 1,
        'text_wrap': True,
    }

    title = {
        **common_properties,
        "bold": True,
        "font_size": 20,
    }

    title_month = {
        **common_properties,
        "bold": True,
        "bg_color": '#ddebf7',
        "font_size": 18,
    }

    title_week = {
        **common_properties,
        "bold": True,
        "bg_color": '#5b9ad5',
        "font_size": 11,
    }

    header_blue = {
        **common_properties,
        "bold": True,
        "bg_color": '#0070c0',
        "font_color": "white",
        "font_size": 9,
    }

    header_orange = {
        **common_properties,
        "bold": True,
        "bg_color": '#f4b184',
        "font_color": "black",
        "font_size": 9,
    }

    content_blue = {
        **common_properties,
        "bold": False,
        "bg_color": '#ddebf7',
    }

    content_blue_name = {
        **content_blue,
        "align": "left",
    }

    content_orange = {
        **common_properties,
        "bold": False,
        "bg_color": '#fff2cc',
    }

    weekend_red = {
        **common_properties,
        "bold": True,
        "bg_color": 'red',
        "font_color": "white",
    }

    cell_containt_k={
        **common_properties,
        "align": "center",
        "bg_color": '#ff9999',
        "font_color": "black",

    }

    cell_containt_hd={
        **common_properties,
        "align": "center",
        "bg_color": '#ffc000',
        "font_color": "black",
    }

    cell_containt_cb={
        **common_properties,
        "align": "center",
        "bg_color": '#00b04f',
        "font_color": "white",
    }

    cell_containt_c={
        **common_properties,
        "align": "center",
        "bg_color": '#92d050',
        "font_color": "black",
    }

    cell_containt_s={
        **common_properties,
        "align": "center",
        "bg_color": '#cc66ff',
        "font_color": "black",
    }

    cell_containt_t={
        **common_properties,
        "align": "center",
        "bg_color": '#ffff00',
        "font_color": "red",
    }

    cell_containt_a={
        **common_properties,
        "align": "center",
        "bg_color": '#bdd7ee',
        "font_color": "black",
    }

    cell_containt_dn={
        **common_properties,
        "align": "center",
        "bg_color": '#bdd7ee',
        "font_color": "red",
    }

    cell_containt_blank={
        **common_properties,
        "align": "center",
        "bg_color": 'red',
        "font_color": "black",
    }

# template = Template_excel()
# print(template.content_blue_name)
