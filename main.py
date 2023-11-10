# import time
import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from uuid import uuid1
import sqlite3
import segno


class Check:
    count = 0

    def __init__(self):
        Check.count += 1
        self.check_name = Check.count
        self.size = 11
        self.font = 'Helvetica'
        self.page_width = 300
        self.page_height = 0
        self.biggest = 0
        self.pagesize = (self.page_width, self.page_height)
        self.can = canvas.Canvas(filename=f'checks/check{self.check_name}.pdf', pagesize=self.pagesize)
        self.can.setFont(psfontname=self.font, size=self.size)
        # Database connect
        try:
            self.con = sqlite3.connect('db/database.db')
            self.cur = self.con.cursor()
        except Exception as e:
            raise Exception(f'{e}')
        self.cashier = 'Asadbek Solijonov'
        self.check_id = f'{uuid1()}'
        self.inn = 307575237
        self.date = datetime.date.today().strftime('%d-%m-%Y')
        self.time = datetime.datetime.now().strftime("%H:%M:%S")

    def _set_image(self, img, y):
        """
        Bu funksiya rasm chizish uchun ishlatiladi.
        :param img: *.jpg, *.png ...
        :param y: coordinate
        :return: None
        """
        img_width, img_height = ImageReader(img).getSize()
        self.biggest = (self.page_width / img_width) / 2
        img_width *= self.biggest
        img_height *= self.biggest
        x = (self.page_width - img_width) / 2
        self.can.drawImage(img, x, y, img_width, img_height)

    def _set_line(self, prefix='-'):
        """
        Bu funksiya chiziq chizib ma'lumotlarni ajratib ko'rsatish uchun ishlatiladi.
        :param prefix: '-',
        :return: None
        """
        prefix_count = 0
        str_with = self.can.stringWidth(text=prefix)
        target = self.page_width - 40
        while target > str_with:
            prefix_count += 1
            str_with = self.can.stringWidth(text=prefix * prefix_count)
        x = (self.page_width - str_with) / 2
        y = self.page_height - 5
        self.can.drawString(x, y, prefix * prefix_count)

    def _scanner_qr_data(self):
        """
        Bu funksiya Purchase ma'lumotlar bazasidan ummumiy summa va jami qqs hissoblab beradu
        :return: None
        """
        data = self.cur.execute(
            f"""SELECT SUM(count*price),  SUM(qqs*count*price/100) FROM Purchase WHERE id={Check.count};""").fetchone()
        return data

    def _search_purchase(self):
        """
        Bu ma'lumotlar bazidan id=? ga teng bo'lgan ma'lumotlarni qaytaradi.
        :return: datas:list
        """
        sqlcode = f"""
        SELECT product, count, price, count*price, qqs, qqs*count*price/100 
        FROM Purchase WHERE id={Check.count};"""
        datas = self.cur.execute(sqlcode).fetchall()
        return datas

    def _create_qr_code(self):
        """
        Bu funksiya jami sotib olingan productlarning jami narxini qr code orqali ko'rsatadi.
        :return: qr_code_uri
        """
        text = 'Thank you for your purchase!'
        data = self._scanner_qr_data()

        try:
            qr_code = segno.make_qr(
                f"Check: #{Check.count}\n"
                f"INN: {self.inn}\n"
                f"Date: {self.date}\n"
                f"Hour: {self.time}\n"
                f"Check ID: {self.check_id}\n"
                f"Cashier: {self.cashier}\n"
                f"{(len(text) - 3) * '- '}\n"
                f"Total: {data[0]:,.2f} uzs\n"
                f"QQS: {data[1]:,.2f} uzs\n"
                f"{(len(text) - 3) * '- '}\n"
                f"{text}")
        except TypeError as e:
            raise TypeError(f"{self._create_qr_code.__name__}() da xatolik: {e}")

        qr_code.save(f'qrcodes/qr_code{Check.count}.png')
        return qr_code.png_data_uri(scale=3)

    def set_invoice(self):
        """
        Bu funksiya logo, qr_code va sotib olingan productlarning narxini yozib beradi
        :return: None
        """
        # QR Code
        x = 20
        self._set_image(img=self._create_qr_code(), y=10)
        self.page_height += ImageReader(self._create_qr_code()).getSize()[1] + 10
        # data
        for data in self._search_purchase():
            self.page_height += 70
            y = self.page_height - 20
            self._set_line()

            self.can.drawString(x, y, f"Product: {data[0]}")
            self.can.drawRightString(self.page_width - x, y, f"{data[2]:,.2f}")

            self.can.drawString(x, y - 15, f"Count: {data[1]}x")
            self.can.drawRightString(self.page_width - x, y - 15, f"{data[3]:,.2f}")

            self.can.drawString(x, y - 30, f"QQS: {round(data[4], 0)}%")
            self.can.drawRightString(self.page_width - x, y - 30, f"{data[5]:,.2f}")
            self.can.setPageSize(size=(self.page_width, self.page_height))
        # logo
        self._set_image(img='logo/logo.png', y=self.page_height + 10)
        self.page_height += ImageReader('logo/logo.png').getSize()[1] * self.biggest + 20
        self.can.setPageSize(size=(self.page_width, self.page_height))

    def write_changes(self):
        """
        Bu funksiya canvasga yozilga ma'lumotlarni saqalash uchun ishlatiladi.
        :return: None
        """
        self.can.showPage()
        self.can.save()


def main():
    """
    Bu funksiya terminalda chiroyli natijalar chiqaradi va Check class ini ishga tushiradi.
    :return: None
    """
    # time.sleep(1)
    print("Processing!...")
    a = Check()
    # time.sleep(1)
    print("Invoice writing!...")
    a.set_invoice()
    a.write_changes()
    # time.sleep(1)
    print('Successfully done!')


if __name__ == '__main__':
    while True:
        client = input("input: ")
        if client in ['continue', 'con', 'c']:
            main()
        else:
            break
