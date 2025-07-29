import os

files = os.listdir('.')
textfile = open("_listFiles.csv", "w", encoding="utf-8")

print(len(files))
for element in files:
    textfile.write(element.replace('\u0301', ' ') + "\n")

textfile.close()
input('Over.')