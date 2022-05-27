import xml.etree.ElementTree as ET
import os, sys
import os.path
from PIL import Image
import PIL
import pandas as pd
import json


def image_file_elab(imagedir="images", xmldir="xmldata", outputdir = "final"):


    MaxWidth = 800
    MaxHeight = 450

    # Sample COCO categories (using only the one in the images provided)
    Categories = [
        {"supercategory": "person", "id": 1,"name": "person"},
        {"supercategory": "vehicle", "id": 2,"name": "car"},
        {"supercategory": "vehicle", "id": 3,"name": "bike"},
        {"supercategory": "animal", "id": 4,"name": "cat"},
        {"supercategory": "animal", "id": 5,"name": "dog"},
        {"supercategory": "object", "id": 6,"name": "ball"}
    ]

    Categories_df = pd.DataFrame(Categories)

    try:
        XmlDirs = os.listdir(xmldir)
    except:
        print("xmldir does not exists!")
        sys.exit(1)

    try:
        ImagesDirs = os.listdir(imagedir)
    except:
        print("imagedir does not exists!")
        sys.exit(1)
    

    # XML files
    Xml_list = []
    for file in XmlDirs:
        Xml_list.append(file)

    # Image files
    Images_list = []
    for file in ImagesDirs:
        Images_list.append(file)


    Annotations = []
    annotation_id = 1
    for file in Xml_list:
        file_name_complete = xmldir + "/" + file
        tmp_dict = {}
        tree = ET.parse(file_name_complete)
        root = tree.getroot()
        filename = root.find("filename").text
        image_id = int(filename.split(".")[0])
        object_list = []
        for elem in root.findall('object'):
            object_elem = []
            object_elem.append(elem.find('name').text)
            for subelem in elem.findall('bndbox'):
                xmin = int(subelem.find('xmin').text)
                xmax = int(subelem.find('xmax').text)
                ymin = int(subelem.find('ymin').text)
                ymax = int(subelem.find('ymax').text)
                # x
                object_elem.append((xmin+xmax)/2)
                # y
                object_elem.append((ymin+ymax)/2)
                # width
                object_elem.append(xmax-xmin)
                # height
                object_elem.append(ymax-ymin)
            object_list.append(object_elem)
    

        object_numbers = len(object_list)
        for i in range(object_numbers):
            tmp_dict["id"] = annotation_id
            tmp_dict["image_id"] = image_id
            tmp_dict["category_id"] = int(Categories_df[Categories_df.name==object_list[i][0]]["id"].values)
            tmp_dict["bbox"] = object_list[i][1:]
            Annotations.append(tmp_dict)
            tmp_dict = {}
            annotation_id += 1


    # Convert to DF
    Annotations_df = pd.DataFrame(Annotations)
    Annotations_df.set_index("id", inplace=True)

    # Resize Images where necessary
    Images = []
    try:
        os.mkdir(outputdir)
    except OSError as error:
        print("outputdir already exists")

    for im in Images_list:
        image_name_complete = imagedir + "/" + im
        tmp_dict = {}
        StrName = im.split(".")[0]
        tmp_dict["id"] = int(StrName)
        image = Image.open(image_name_complete)
        width = image.size[0]
        height = image.size[1]
        width_ratio = (MaxWidth / float(image.size[0]))
        height_ratio = (MaxHeight / float(image.size[1]))
        ratio = 1 # no resizing
        if (min(width_ratio, height_ratio) < 1):
            ratio = min(width_ratio, height_ratio)
            width = int((float(image.size[0]) * float(ratio)))
            height = int((float(image.size[1]) * float(ratio)))       
            image = image.resize((width, height), PIL.Image.NEAREST)
        tmp_dict["width"] = width
        tmp_dict["height"] = height
        tmp_dict["ratio"] = ratio
        image_name_final_complete = outputdir + "/" + StrName + "_fin.jpg"
        tmp_dict["file_name"] = StrName + "_fin.jpg"
        image.save(image_name_final_complete)
        Images.append(tmp_dict)


    # Convert to DF
    Images_df = pd.DataFrame(Images)
    Images_df.set_index("id", inplace=True)

    # Image Resized ID - Ratio
    Images_res_df = Images_df.loc[Images_df["ratio"]<1,:]
    for ind, row in Images_res_df.iterrows():
        for annotation in Annotations:
            if (annotation['id'] == ind):
                bbox = annotation['bbox']
                annotation['bbox'] = [round(element*row["ratio"],2) for element in bbox]


    # Output JSON (COC simplified format)

    # images
    # remove "ratio" from Images
    for elem in Images:
        del elem['ratio']


    OutJSON = {}
    OutJSON["categories"] = Categories
    OutJSON["images"] = Images
    OutJSON["annotations"] = Annotations

    output_file = outputdir + "/output.json"
    with open(output_file, 'w') as outfile:
        json.dump(OutJSON, outfile,indent=4)
    pass

if __name__ == "__main__":
    list_of_args = sys.argv
    if len(list_of_args)==1:
        print(f"Il programma utilizzerà i valori di default per:")
        print(f"imagedir (./images), xmldir (./xmldata) and outputdir (./final)")
        image_file_elab()
    elif len(list_of_args)==2:
        print(f"Il programma utilizzerà i valori di default per:")
        print(f"xmldir (/xmldata) and outputdir (/final)")
        image_file_elab(imagedir=list_of_args[1])
    elif len(list_of_args)==3:
        print(f"Il programma utilizzerà i valori di default per:")
        print(f"outputdir (final)")
        image_file_elab(imagedir=list_of_args[1], xmldir=list_of_args[2])
    else:
        image_file_elab(imagedir=list_of_args[1], xmldir=list_of_args[2], outputdir=list_of_args[3])