import os
import random
import pandas as pd
from datetime import datetime, timedelta

def generate_sample_excel(filename="sample_real_estate_car_data.xlsx", num_sheets=5, rows_per_sheet=10000):
    """
    Generate realistic multi-sheet sample Excel file matching the schema:
    REG NO, RTO, REG DATE, NAME, ADDRESS, PINCODE, MAKE, MODEL VARIANT, MOBILE
    """
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "sample_data"), exist_ok=True)
    file_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", filename)
    
    first_names = ["AMAR", "AMITVIR", "ANIL", "ATISH", "BALSHIRAM", "DEVENDRA", "GANESH", "HARSHAL", "JAINAB", "JYOTIKA", "KAPIL", "MAHENDRA", "MANISH", "NILESH", "PRASANJEET", "RAHUL", "RAJESH", "RUPESH", "SACHIN", "SANDESH", "SANDEEP", "SANTOSH", "ABDHULRAHEMAN", "ABHAY", "ABHIJEET", "ABHIJIT", "ABHISHEK", "ABRAR", "ADITI", "ADITYA", "AHILYA", "AJAY", "AJIT"]
    last_names = ["SHETE", "SINGH BHAMRA", "MURLIDHAR DUMBRE", "BARNE", "WABALE", "GARUD", "BADHE", "SHANKHAPAL", "BHORI", "CHALKE", "BORDE", "YADAV", "TODKARI", "PASALKAR", "MISHRA", "KULKARNI", "DHOBALE", "THAKARE", "PHATAK", "BHUMKAR", "DESHMUKH", "SHAIKH", "KADEKAR", "SHARMA", "PRADHAN", "DHAMALE", "LUNAWAT", "SINKAR", "PURANDARE", "DESHPANDE", "BHATANE", "PUDALE"]
    
    makes = ["MARUTI", "HYUNDAI", "TOYOTA", "HONDA", "TATA", "SKODA", "MERCEDES", "MAHINDRA", "KIA", "VOLKSWAGEN"]
    models = {
        "MARUTI": ["CELERIO VXI GREEN (O)", "BALENO ALPHA", "OMNI E MPI STD. BSIV", "BALENO ZETA PETROL", "DZIRE VXI", "CELERIO VXI GREEN", "BALENO DELTA PETROL", "WAGON R GREEN LXI", "ERTIGA SMART HYBRID VXI", "SWIFT VDI AMT", "ALTO K10 VXI AMT (O)"],
        "HYUNDAI": ["I20 MAGNA EXECUTIVE CVT", "I20 ASTA VTVT", "GRAND I10 SPORTZ 1.2", "SANTRO 1.1AMT SPORTZ", "I20 SPORTZ VTVT", "CRETA SX PETROL", "VENUE SX TURBO"],
        "TOYOTA": ["COROLLA ALTIS D-4D GL", "INNOVA CRYSTA 2.8 G", "FORTUNER 4X2 AT", "URBAN CRUISER HIGH"],
        "HONDA": ["AMAZED 1.2 S MT (I-VTEC)", "CITY 1.5 ZX CVT (I-VTEC)", "AMAZED 1.5 V CVT (I-DTEC)", "WR-V VX PETROL"],
        "TATA": ["TIAGO XZA 1.2 RTN BS4", "NEXON XZA 1.2 RTN BS4", "ALTROZ XZ PETROL", "HARRIER XZA PLUS"],
        "SKODA": ["RAPID AMBITION (81KW TDI CR)", "SLAVIA 1.5 TSI", "KUSHAQ MONTE CARLO"],
        "MERCEDES": ["C 220 D", "E 220 D", "GLA 200"],
        "MAHINDRA": ["THAR LX HARD TOP", "XUV700 AX7 L", "SCORPIO N Z8"],
        "KIA": ["SELTOS GTX PLUS", "SONET HTX TURBO"],
        "VOLKSWAGEN": ["TAIGUN GT 1.5", "VIRTUS GT 1.5"]
    }
    
    rto_list = ["MH12", "MH14", "MH01", "MH02", "MH47", "MH04"]
    pincodes = ["411033", "411027", "410504", "412105", "410503", "411017", "411015", "411018", "412105", "410501", "411012", "411061", "411035", "411034", "411019", "410502", "411057", "411048", "412207", "411045", "411030", "412210", "411021", "411014", "411044", "411038", "411041", "411007", "411043", "411046"]
    areas = ["WAKAD", "PIMPRI", "AUNDH", "BANER", "CHINCHWAD", "KOTHRUD", "HADAPSAR", "VIMAN NAGAR", "KHARADI", "PASHAN", "BAWDHAN", "HINGANE", "KATRAJ", "NIGDI", "AKURDI"]
    
    years = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    
    print(f"Generating synthetic sample Excel file with {num_sheets} sheets ({num_sheets * rows_per_sheet} total rows)...")
    
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for s in range(num_sheets):
            sheet_year = years[s % len(years)]
            sheet_name = f"{sheet_year}" if s < len(years) else f"Sheet_{s+1}"
            
            data = []
            for i in range(rows_per_sheet):
                rto = random.choice(rto_list)
                series_char1 = chr(random.randint(65, 90))
                series_char2 = chr(random.randint(65, 90))
                num = random.randint(1000, 9999)
                reg_no = f"{rto}{series_char1}{series_char2}{num}"
                
                day = random.randint(1, 28)
                month = random.randint(1, 12)
                reg_date = f"{day}/{month}/{sheet_year}"
                
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                name = f"{fname} {lname}"
                
                pincode = random.choice(pincodes)
                area = random.choice(areas)
                flat_no = f"FLAT NO-{chr(random.randint(65, 70))}-{random.randint(101, 1204)}"
                society = f"{random.choice(['GOKUL', 'SAI', 'AMRUT', 'SHREE', 'KAPIL', 'ROHAN', 'CONCORD', 'GREEN'])} {random.choice(['PARK', 'HEIGHTS', 'RESIDENCY', 'VILLA', 'SOCIETY', 'TOWER'])}"
                address = f"{flat_no}, {society}, {area}, PUNECODE-{pincode}"
                
                make = random.choice(makes)
                model_variant = random.choice(models[make])
                
                mobile = f"9{random.randint(100000000, 999999999)}"
                
                data.append({
                    "REG NO": reg_no,
                    "RTO": rto,
                    "REG DATE": reg_date,
                    "NAME": name,
                    "ADDRESS": address,
                    "PINCODE": pincode,
                    "MAKE": make,
                    "MODEL VARIANT": model_variant,
                    "MOBILE": mobile
                })
            
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  - Sheet '{sheet_name}' created with {rows_per_sheet} rows.")
            
    print(f"Sample data generated successfully at: {file_path}")

if __name__ == "__main__":
    generate_sample_excel("Pune_Car_Data_2018_to_2025_Sample.xlsx", num_sheets=5, rows_per_sheet=10000)
