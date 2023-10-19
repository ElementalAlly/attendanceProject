import argparse
import datetime
import pathlib
import sys

import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageOps

class Cursor:
    def __init__(self, dimension, initial):
        self.dimension = dimension
        self.cursor = [initial[0], initial[1]]

    def advance(self):
        self.cursor[0] += 1
        if self.cursor[0] >= self.dimension[0]:
            self.cursor[0] = 0
            self.cursor[1] += 1
        if self.cursor[1] >= self.dimension[1]:
            self.cursor[1] = 0
            return True
        return False


class Paginator:
    def __init__(self, dimension):
        self.dimension = dimension
        self.pages = []
        self.image_size = None
        self.cursor = Cursor(dimension, dimension)

    def add(self, image):
        if self.image_size is None:
            self.image_size = image.size
        if self.cursor.advance():
            self.pages.append(Image.new("RGB", (self.image_size[0] * self.dimension[0], self.image_size[1] * self.dimension[1]), color="white"))
        self.pages[-1].paste(image, (self.cursor.cursor[0] * self.image_size[0], self.cursor.cursor[1] * self.image_size[1]))

    def output(self, output_dir):
        for i, img in enumerate(self.pages):
            out_file = output_dir / f"qr-page{i}.png"
            img.save(str(out_file), dpi=(300, 300))
            print(f"Created {out_file}!")


def main(prefix, the_range, suffix, number_format, logo_path, page_dimension, duplicate, output_dir):
    pages = Paginator(page_dimension)

    # This is modified from https://www.geeksforgeeks.org/how-to-generate-qr-codes-with-a-custom-logo-using-python/
    if logo_path:
        logo = Image.open(str(logo_path))

        basewidth = 80

        wpercent = basewidth / float(logo.size[0])
        hsize = int((float(logo.size[1]) * float(wpercent)))
        logo = logo.resize((basewidth, hsize), Image.LANCZOS)

    for i in range(*the_range):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        sequence = number_format % i
        data = prefix + sequence + suffix
        qr.add_data(data)
        qr.make()
        qr_img = qr.make_image().convert("RGB")

        if logo_path:
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos)

        x_size, y_size = qr_img.size

        img = Image.new("RGB", (x_size * 3 - 100, y_size + 100), color="white")
        img = ImageOps.expand(img, border=5, fill="black")

        img.paste(qr_img, (x_size * 2 - 100, 5))

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", 50)
        draw.text((30, 50), "Record Robotics ID", font=font, stroke_width=2, fill=(0, 0, 0))
        draw.text((30, 150), data, font=font, fill=(0, 0, 0))
        draw.text((30, 360), "Name: _______________________", font=font, fill=(0, 0, 0))

        out_file = output_dir / f"qr-{sequence}.png"
        img.save(str(out_file), dpi=(300, 300))
        print(f"Created {out_file}!")

        pages.add(img)
        if duplicate:
            pages.add(img)
    pages.output(output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="make-qr-cards", description="Make cards with QR code with a range of number"
    )
    parser.add_argument(
        "--prefix",
        default=f"RR-{datetime.date.today().year}-",
        help="string prefix text before the number",
    )
    parser.add_argument(
        "--range",
        type=int,
        nargs=2,
        required=True,
        help="range of number from start to excluded-end. e.g. '--range 0 10' means number 0 to 9",
    )
    parser.add_argument("--suffix", default="", help="string suffix text after the number")
    parser.add_argument(
        "--number-format",
        default="%04d",
        help="how to format the number in the string. default: %04d",
    )
    parser.add_argument(
        "--logo",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parent.parent / "attendancetracker/app/logo.jpg",
        help="logo to use",
    )
    parser.add_argument(
        "--page-dimension",
        type=int,
        nargs=2,
        default=(2, 6),
        help="x y of how many cards go into a page",
    )
    parser.add_argument(
        "--duplicate",
        action="store_true",
        default=False,
        help="Duplicate the card or not",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("."),
        help="output directory to put all the output",
    )
    args = parser.parse_args(sys.argv[1:])
    main(args.prefix, args.range, args.suffix, args.number_format, args.logo, args.page_dimension, args.duplicate, args.output_dir)
