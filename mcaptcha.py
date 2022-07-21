import random
import string
import os
from PIL import Image, ImageFont, ImageDraw


def new(captcha_name=None):
	# Generating captcha
	captcha_characters = string.ascii_uppercase + string.digits
	captcha_text = "".join(
	    random.choice(captcha_characters) for x in range(random.randint(6, 8)))

	# Generating image
	image = Image.open(
	    f'assets/captcha/bg/{random.choice(os.listdir("assets/captcha/bg"))}')
	draw = ImageDraw.Draw(image)

	# Adding random font from fonts directory
	font = ImageFont.truetype(
	    f'assets/captcha/font/{random.choice(os.listdir("assets/captcha/font"))}',
	    random.randint(80, 120))

	# Width and height of image
	W, H = (1000, 500)

	top_y = 95
	bottom_y = 280
	left_x = 120
	right_x = 740

	# Generating random symbols
	for i in range(random.randint(4, 7)):
		x = 300
		y = 130
		while (x > left_x and x < right_x) or (y > top_y and y < bottom_y):
			x, y = random.randint(10, W), random.randint(10, H)
		draw.text((x, y),
		          random.choice(captcha_characters), (255, 255, 255),
		          font=font)

	# deprecated method
	w, h = draw.textsize(captcha_text, font=font)

	# Drawing text
	draw.text(((W - w) / 2, (H - h) / 2),
	          captcha_text, (255, 255, 255),
	          font=font)

	file_name = f'assets/temp/{captcha_name}_{captcha_text}.png'

	# Saving picture
	image.save(file_name)

	return file_name