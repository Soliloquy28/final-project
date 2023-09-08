from __future__ import print_function
import os
import sys
import PIL.Image
import PIL.ImageTk
from PIL import ImageGrab


# Get the absolute width and height of device screen
img = ImageGrab.grab()
screen_width = img.size[0]
screen_height = img.size[1]

# Perspective transformation image size (pixels) [Track width, Track length]
blob_size = [450, 1500]
# Actual size (cm) [Track width, Track length]
blob_real_size = [42, 140]
# Boundary expansion size (pixels) [Total boundary width, Total boundary height]
blob_border_size = [300, 100]
# Actual width ratio
blob_width_ratio = blob_size[0] / blob_real_size[0]
# Actual height ratio
blob_height_ratio = blob_size[1] / blob_real_size[1]


multiple_size = [600, 1442]
multiple_real_size = [62, 149]
multiple_width_ratio = multiple_size[0] / multiple_real_size[0]
multiple_height_ratio = multiple_size[1] / multiple_real_size[1]


def resource_path(relative_path):
    """ Get the absolute path for the resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def photo_place(image_name, image_width, image_height):
    # Use PIL library to open the image
    image_path = resource_path(image_name)
    image = PIL.Image.open(image_path)
    # image = PIL.Image.open(f"{directory_path}/Figures/image_name")
    # Define the size of image
    target_width = image_width
    target_height = image_height
    # Calculate the scale ratio
    width, height = image.size
    aspect_ratio = min(target_width / width, target_height / height)
    new_width = int(width * aspect_ratio)
    new_height = int(height * aspect_ratio)
    # Adjust the size of image
    image = image.resize((new_width, new_height))
    # Convert the Image object of PIL to the PhotoImage object of Tkinter
    photo = PIL.ImageTk.PhotoImage(image)
    return photo