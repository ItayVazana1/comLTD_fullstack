from sqlalchemy.orm import sessionmaker
from app.models.database import engine
from app.models.tables import Package

def populate_packages():
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    packages = [
        {"package_name": "Basic", "description": "Basic package with limited features.", "monthly_price": 50},
        {"package_name": "Standard", "description": "Standard package with additional features.", "monthly_price": 100},
        {"package_name": "Premium", "description": "Premium package with all features included.", "monthly_price": 150},
        {"package_name": "VIP", "description": "VIP package with exclusive benefits.", "monthly_price": 200},
    ]

    for package in packages:
        existing_package = session.query(Package).filter_by(package_name=package["package_name"]).first()
        if existing_package:
            continue

        new_package = Package(
            package_name=package["package_name"],
            description=package["description"],
            monthly_price=package["monthly_price"],
        )
        session.add(new_package)

    session.commit()
    session.close()
