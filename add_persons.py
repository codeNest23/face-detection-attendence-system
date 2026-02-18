from opencv.fr import FR
import cv2
import os
import base64
from opencv.fr import FR

BACKEND_URL = "https://us.opencv.fr"
DEVELOPER_KEY = "elaBl7xMjVlNGI2ZmUtZTA1YS00MWRiLWE3N2QtMjdiMDhhY2M5NTc4"


sdk = FR(BACKEND_URL, DEVELOPER_KEY)
from opencv.fr.persons.schemas import PersonBase
from pathlib import Path

image_base_path = Path("sample_images")
image_path = image_base_path / "aman.jpg"

# The only mandatory parameter for a person is images
# If id is unspecified, it will be auto-generated
# If name is unspecified, it will be set to the person's id
person = PersonBase([image_path], name="aman")
person = sdk.persons.create(person)
print("person is created successfully")



