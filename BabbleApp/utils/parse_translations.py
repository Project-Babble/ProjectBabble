def parse_translations(output_folder, input_translations_csv):
    import csv
    import json
    from os import path, makedirs
    translations_data = []
    with open(input_translations_csv, "r", encoding="utf-8") as translations_file:
        csv_reader = csv.reader(translations_file)
        for row in csv_reader:
            translations_data.append(row)
    for column_index in range(3, len(translations_data[0])): # Skip first two columns (File,context, context)
        language = translations_data[0][column_index]
        result = {}
        for row_index in range(1, len(translations_data)): #skip headers
            context = translations_data[row_index][1].replace("\"","")
            translation = translations_data[row_index][column_index]
            result[context] = translation
        # Makes folder if it doesn't exist.
        if not path.exists(path.join(output_folder, language)):
            makedirs(path.join(output_folder, language))
        with open(path.join(output_folder,language,"locale.json"), "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, indent="\t", ensure_ascii=False)
            
            
if __name__ == "__main__":
    output_folder = r"parsed_translations"
    input_translations_csv = r"C:\Users\T\Desktop\PythonProjects\BabbleApp\ProjectBabble\BabbleApp\utils\all_translations.csv"
    parse_translations(output_folder, input_translations_csv)
