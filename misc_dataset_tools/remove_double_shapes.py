import csv

# Open the CSV file for reading
with open('your_file.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    fieldnames = csv_reader.fieldnames

    # Open a new CSV file for writing
    with open('new_file.csv', mode='w', newline='') as new_csv_file:
        writer = csv.DictWriter(new_csv_file, fieldnames=fieldnames)
        writer.writeheader()

        # Iterate over each row in the original CSV file
        for row in csv_reader:
            # Check if the row has values for both mouthLeft and mouthRight columns
            if row.get('mouthLeft') and row.get('mouthRight'):
                # If it does, skip this row
                continue
            else:
                # Otherwise, write this row to the new CSV file
                writer.writerow(row)

print('Filtered CSV created successfully')
