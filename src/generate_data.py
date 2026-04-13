import csv
import os
import random
from datetime import datetime, timedelta

# Ensure output directory exists
output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

def generate_patients(n=50):
    genders = ["M", "F", "Other"]
    zip_codes = ["90210", "10001", "60601", "75201", "33101"]
    patients = []
    for i in range(1, n + 1):
        patients.append([
            f"P{i:04d}",
            f"Patient_{i}",
            random.randint(18, 90),
            random.choice(genders),
            random.choice(zip_codes)
        ])
    
    with open(os.path.join(output_dir, "patients.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["patient_id", "name", "age", "gender", "zip_code"])
        writer.writerows(patients)
    return patients

def generate_diagnoses(patients, max_per_patient=3):
    conditions = [
        ("Hypertension", "Patient has high blood pressure, requires monitoring and lifestyle changes."),
        ("Type 2 Diabetes", "Patient shows elevated blood sugar levels, prescribed medication and diet plan."),
        ("Asthma", "Patient experiences shortness of breath and wheezing, prescribed inhaler."),
        ("Depression", "Patient reports persistent sadness and lack of interest, referred to counseling."),
        ("Osteoarthritis", "Patient reports joint pain and stiffness, prescribed physical therapy."),
        ("Chronic Kidney Disease", "Patient shows reduced kidney function, requires regular monitoring."),
        ("Breast Cancer", "Early stage detection, scheduled for surgery and follow-up oncology."),
        ("Melanoma", "Skin lesion identified as malignant, scheduled for excision.")
    ]
    diagnoses = []
    d_id = 1
    for p in patients:
        p_id = p[0]
        n_diag = random.randint(1, max_per_patient)
        for _ in range(n_diag):
            date = datetime.now() - timedelta(days=random.randint(1, 365*5))
            cond, desc = random.choice(conditions)
            diagnoses.append([
                f"D{d_id:04d}",
                p_id,
                cond,
                desc,
                date.strftime("%Y-%m-%d")
            ])
            d_id += 1
            
    with open(os.path.join(output_dir, "diagnoses.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["diagnosis_id", "patient_id", "condition", "description", "date"])
        writer.writerows(diagnoses)

def generate_medications(patients, max_per_patient=4):
    drugs = ["Lisinopril", "Metformin", "Albuterol", "Sertraline", "Ibuprofen", "Atorvastatin", "Amlodipine", "Omeprazole"]
    medications = []
    m_id = 1
    for p in patients:
        p_id = p[0]
        n_meds = random.randint(1, max_per_patient)
        for _ in range(n_meds):
            date = datetime.now() - timedelta(days=random.randint(1, 365*2))
            medications.append([
                f"M{m_id:04d}",
                p_id,
                random.choice(drugs),
                f"{random.choice([10, 20, 50, 100])}mg",
                date.strftime("%Y-%m-%d")
            ])
            m_id += 1
            
    with open(os.path.join(output_dir, "medications.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["medication_id", "patient_id", "drug_name", "dosage", "date"])
        writer.writerows(medications)

if __name__ == "__main__":
    patients = generate_patients(50)
    generate_diagnoses(patients)
    generate_medications(patients)
    print("Generated synthetic data with vector search descriptions in 'data/' directory.")
