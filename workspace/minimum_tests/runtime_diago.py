from sagittarius import doctor

report = doctor()
print(report["schema_version"])
print(report["requested_backend"])
print(report["available"])
print(report["backend_probe"])