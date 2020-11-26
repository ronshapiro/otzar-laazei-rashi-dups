from collections import Counter
import requests
import xlsxwriter

def api_request(endpoint):
    return requests.get(f"https://www.sefaria.org/api/texts{endpoint}").json()

def duplciation_key(comment):
    return (comment["anchorRef"], comment["ref"])

def duplicates_sort_function(duplicates):
    otzar_ref = duplicates[0]
    return int(otzar_ref[otzar_ref.rfind(" ") + 1:])

duplicates = {}
normalized_refs = {}
for variant in api_request("/Otzar_Laazei_Rashi,_Talmud")["titleVariants"]:
    if not variant.startswith("Talmud, "):
        continue
    masechet = variant[len("Talmud, "):]
    links = api_request(f"/Otzar_Laazei_Rashi,_{variant}?commentary=1")["commentary"]
    counts = Counter(map(duplciation_key, links))

    for k in counts.keys():
        count = counts.get(k)
        if count > 1:
            if masechet not in duplicates:
                duplicates[masechet] = []
            duplicates[masechet].append((k[0], k[1], count))
    duplicates.get(masechet, []).sort(key=duplicates_sort_function)

    for link in links:
        if link["anchorRef"] not in normalized_refs:
            normalized_refs[link["anchorRef"]] = []
        normalized_refs[link["anchorRef"]].append(link["ref"])

workbook = xlsxwriter.Workbook("Duplicates.xlsx")
bold = workbook.add_format({'bold': True})
normalized_refs_sheet = workbook.add_worksheet("Normalized Links")
between_same_refs_sheet = workbook.add_worksheet("Between same refs")
between_same_refs_sheet.set_column(0, 0, 15)
between_same_refs_sheet.set_column(1, 1, 45)
between_same_refs_sheet.set_column(2, 2, 45)
between_same_refs_sheet.set_column(3, 3, 15)
between_same_refs_sheet.write(0, 0, "Masechet", bold)
between_same_refs_sheet.write(0, 1, "Otzar Laazei Rashi ref", bold)
between_same_refs_sheet.write(0, 2, "Rashi ref", bold)
between_same_refs_sheet.write(0, 3, "duplicate count", bold)

row = 1
for masechet, values in duplicates.items():
    for duplicate in values:
        between_same_refs_sheet.write(row, 0, masechet)
        between_same_refs_sheet.write_url(row, 1, f"https://sefaria.org/{duplicate[0].replace(' ', '_')}", string=duplicate[0])
        between_same_refs_sheet.write_url(row, 2, f"https://sefaria.org/{duplicate[1].replace(' ', '_')}", string=duplicate[1])
        between_same_refs_sheet.write(row, 3, duplicate[2])
        row += 1

def normalized_refs_sort_function(anchor_ref):
    return (
        anchor_ref[len("Otzar Laazei Rashi, Talmud, "):anchor_ref.rfind(" ")],
        int(anchor_ref[anchor_ref.rfind(" ") + 1:]))

def normalized_refs_reducer(ref):
    return ref.split(":")[0]

normalized_refs_keys = list(normalized_refs.keys())
normalized_refs_keys.sort(key=normalized_refs_sort_function)

normalized_refs_sheet.set_column(0, 0, 45)
normalized_refs_sheet.set_column(1, 1, 100)
normalized_refs_sheet.set_column(2, 2, 15)
normalized_refs_sheet.write(0, 0, "Otzar Laazei Rashi ref", bold)
normalized_refs_sheet.write(0, 1, "Duplicate refs", bold)
normalized_refs_sheet.write(0, 2, "Duplicate counts", bold)

row = 1
for k in normalized_refs_keys:
    counts = Counter(map(normalized_refs_reducer, normalized_refs[k]))
    for key in counts.keys():
        if counts.get(key) > 1:
            normalized_refs_sheet.write_url(row, 0, f"https://sefaria.org/{k.replace(' ', '_')}", string=k)
            duplicates = list(filter(lambda x: x.startswith(key), normalized_refs[k]))
            normalized_refs_sheet.write(row, 1, ", ".join(duplicates))
            normalized_refs_sheet.write(row, 2, len(duplicates))
            row += 1
            
workbook.close()

                                
