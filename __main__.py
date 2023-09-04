from __future__ import print_function
import os
import sys
import PIL.Image
import PIL.ImageTk
from PIL import ImageGrab
from Platform import Platform


# Get the absolute width and height of device screen
img = ImageGrab.grab()
screen_width = img.size[0]
screen_height = img.size[1]

# Windows: [1920, 1080]
# Macbook: [3024, 1964] [1512, 982]

# 透视变换图尺寸 (pixel) [ 轨道宽度，轨道长度 ]
blob_size = [450, 1500]
# 真实尺寸 (cm) [ 轨道宽度，轨道长度 ]
blob_real_size = [42, 140] # 3.3333333333333333
# 边界拓展尺寸 (pixel) [ 边界总宽度，边界总高度 ]
blob_border_size = [300, 100]
# 真实宽度比率
blob_width_ratio = blob_size[0] / blob_real_size[0]
# 真实高度比率
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


# 1.75m 长  宽40cm
if __name__ == "__main__":
    app = Platform()
    app.mainloop()
