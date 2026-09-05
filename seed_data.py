from datetime import datetime, timedelta
import random

from app.core.database import SessionLocal
from app.core.geo import linestring_from_coords, point_from_latlng
from app.core.security import get_password_hash
from app.models.incident import Incident
from app.models.patrol import Patrol
from app.models.protected_area import ProtectedArea
from app.models.ranger import Ranger
from app.models.report import CommunityReport
from app.models.species import Species

DEFAULT_PASSWORD = "ranger123"

ZIMBABWE_PARKS = [
    {"name": "Hwange National Park", "zone_type": "national_park", "risk_level": "high", "size_hectares": 1465100, "description": "Zimbabwe's largest national park, famous for elephants and big game. Over 100 mammal species.", "center_lat": -18.56, "center_lng": 26.49},
    {"name": "Gonarezhou National Park", "zone_type": "national_park", "risk_level": "high", "size_hectares": 505300, "description": "Remote wilderness in the southeast lowveld. Known for elephants and the Chilojo Cliffs.", "center_lat": -21.73, "center_lng": 31.55},
    {"name": "Mana Pools National Park", "zone_type": "national_park", "risk_level": "high", "size_hectares": 219600, "description": "UNESCO World Heritage site on the Zambezi River. Iconic wildlife viewing.", "center_lat": -15.75, "center_lng": 29.38},
    {"name": "Matobo National Park", "zone_type": "national_park", "risk_level": "medium", "size_hectares": 42400, "description": "Granite kopjes and black rhino sanctuary. Cultural and natural heritage site.", "center_lat": -20.55, "center_lng": 28.51},
    {"name": "Victoria Falls National Park", "zone_type": "national_park", "risk_level": "medium", "size_hectares": 2340, "description": "Protects the Victoria Falls rainforest and surrounding habitat along the Zambezi.", "center_lat": -17.93, "center_lng": 25.85},
    {"name": "Chizarira National Park", "zone_type": "national_park", "risk_level": "high", "size_hectares": 194000, "description": "Remote and rugged park in Binga district. Home to elephants, lions, and wild dogs.", "center_lat": -17.93, "center_lng": 27.87},
    {"name": "Matusadona National Park", "zone_type": "national_park", "risk_level": "high", "size_hectares": 140700, "description": "On the shores of Lake Kariba. Known for elephants and lions.", "center_lat": -16.92, "center_lng": 28.47},
    {"name": "Kariba",
     "zone_type": "game_reserve",
     "risk_level": "medium",
     "size_hectares": 56000,
     "description": "Lake Kariba fishing and wildlife zone. Hippos and crocodiles.",
     "center_lat": -16.52,
     "center_lng": 28.85},
    {"name": "Gwayi-Shangani Conservancy", "zone_type": "conservation_area", "risk_level": "medium", "size_hectares": 320000, "description": "Community conservancy between Hwange and Kazuma Pan. Emerging wildlife corridor.", "center_lat": -18.18, "center_lng": 27.40},
    {"name": "Chivero (Meikles) Recreational Park", "zone_type": "game_reserve", "risk_level": "low", "size_hectares": 35000, "description": "Close to Harare. Popular for fishing and weekend tourism.", "center_lat": -17.88, "center_lng": 30.55},
]

ZIMBABWE_SPECIES = [
    {"name": "Black Rhino", "scientific_name": "Diceros bicornis", "conservation_status": "CR", "population_estimate": 540, "habitat": "Savanna and woodlands", "threats": "Poaching for horns. Highly targeted by criminal syndicates."},
    {"name": "White Rhino", "scientific_name": "Ceratotherium simum", "conservation_status": "NT", "population_estimate": 380, "habitat": "Grasslands and floodplains", "threats": "Poaching for horns"},
    {"name": "African Elephant", "scientific_name": "Loxodonta africana", "conservation_status": "EN", "population_estimate": 85000, "habitat": "Savanna, forests, and river valleys", "threats": "Poaching for ivory. Main target species in Zimbabwe."},
    {"name": "Lion", "scientific_name": "Panthera leo", "conservation_status": "VU", "population_estimate": 1500, "habitat": "Savanna and grasslands", "threats": "Human-wildlife conflict, poisoning, snaring"},
    {"name": "Leopard", "scientific_name": "Panthera pardus", "conservation_status": "VU", "population_estimate": 3000, "habitat": "Woodlands and rocky outcrops", "threats": "Poaching for skins, conflict with livestock farmers"},
    {"name": "Hippopotamus", "scientific_name": "Hippopotamus amphibius", "conservation_status": "VU", "population_estimate": 6000, "habitat": "Rivers and Lake Kariba", "threats": "Human-wildlife conflict, poaching for teeth"},
    {"name": "Cheetah", "scientific_name": "Acinonyx jubatus", "conservation_status": "VU", "population_estimate": 170, "habitat": "Savanna grasslands", "threats": "Habitat fragmentation, conflict with farmers"},
    {"name": "African Wild Dog", "scientific_name": "Lycaon pictus", "conservation_status": "EN", "population_estimate": 700, "habitat": "Savanna and woodlands", "threats": "Habitat fragmentation, snaring, disease"},
    {"name": "Giraffe", "scientific_name": "Giraffa camelopardalis", "conservation_status": "VU", "population_estimate": 2500, "habitat": "Savanna and woodlands", "threats": "Habitat loss, poaching for meat"},
    {"name": "Sable Antelope", "scientific_name": "Hippotragus niger", "conservation_status": "NT", "population_estimate": 2200, "habitat": "Woodlands and savanna", "threats": "Poaching for meat and horns"},
    {"name": "Roan Antelope", "scientific_name": "Hippotragus equinus", "conservation_status": "NT", "population_estimate": 800, "habitat": "Grasslands and woodlands", "threats": "Habitat loss, competition with cattle"},
    {"name": "African Buffalo", "scientific_name": "Syncerus caffer", "conservation_status": "NT", "population_estimate": 9000, "habitat": "Savanna and river valleys", "threats": "Poaching for meat, disease transmission from cattle"},
]

ADMIN_USERS = {"thandeka.ncube@zimparks.co.zw", "gift.muringani@zimparks.co.zw", "rutendo.dube@zimparks.co.zw"}

RANGERS_DATA = [
    {"name": "Thandeka Ncube", "badge_number": "ZKW-047", "email": "thandeka.ncube@zimparks.co.zw", "phone": "+263771000001", "rank": "senior_officer", "specialization": "patrol", "is_on_duty": True, "park": "Hwange National Park", "lat": -18.56, "lng": 26.49},
    {"name": "Blessing Moyo", "badge_number": "ZKW-039", "email": "blessing.moyo@zimparks.co.zw", "phone": "+263771000002", "rank": "officer", "specialization": "intelligence", "is_on_duty": True, "park": "Gonarezhou National Park", "lat": -21.73, "lng": 31.55},
    {"name": "Chipo Chirinda", "badge_number": "ZKW-055", "email": "chipo.chirinda@zimparks.co.zw", "phone": "+263771000003", "rank": "officer", "specialization": "community_outreach", "is_on_duty": True, "park": "Mana Pools National Park", "lat": -15.75, "lng": 29.38},
    {"name": "Rutendo Dube", "badge_number": "ZKW-043", "email": "rutendo.dube@zimparks.co.zw", "phone": "+263771000004", "rank": "inspector", "specialization": "investigation", "is_on_duty": False, "park": "Matobo National Park", "lat": -20.55, "lng": 28.51},
    {"name": "Maxwell Moyo", "badge_number": "ZKW-061", "email": "maxwell.moyo@zimparks.co.zw", "phone": "+263771000005", "rank": "officer", "specialization": "quick_response", "is_on_duty": True, "park": "Hwange National Park", "lat": -18.45, "lng": 26.60},
    {"name": "Simbai Ndlovu", "badge_number": "ZKW-082", "email": "simbai.ndlovu@zimparks.co.zw", "phone": "+263771000006", "rank": "trainee", "specialization": "patrol", "is_on_duty": True, "park": "Victoria Falls National Park", "lat": -17.93, "lng": 25.85},
    {"name": "Tendai Murisa", "badge_number": "ZKW-091", "email": "tendai.murisa@zimparks.co.zw", "phone": "+263771000007", "rank": "officer", "specialization": "patrol", "is_on_duty": True, "park": "Chizarira National Park", "lat": -17.93, "lng": 27.87},
    {"name": "Nyasha Chiponda", "badge_number": "ZKW-103", "email": "nyasha.chiponda@zimparks.co.zw", "phone": "+263771000008", "rank": "senior_officer", "specialization": "k9_unit", "is_on_duty": True, "park": "Matusadona National Park", "lat": -16.92, "lng": 28.47},
    {"name": "Farai Mlambo", "badge_number": "ZKW-115", "email": "farai.mlambo@zimparks.co.zw", "phone": "+263771000009", "rank": "officer", "specialization": "patrol", "is_on_duty": False, "park": "Gonarezhou National Park", "lat": -21.65, "lng": 31.48},
    {"name": "Gift Muringani", "badge_number": "ZKW-128", "email": "gift.muringani@zimparks.co.zw", "phone": "+263771000010", "rank": "commander", "specialization": "quick_response", "is_on_duty": True, "park": "Gwayi-Shangani Conservancy", "lat": -18.18, "lng": 27.40},
    {"name": "Tatenda Zvaraya", "badge_number": "ZKW-134", "email": "tatenda.zvaraya@zimparks.co.zw", "phone": "+263771000011", "rank": "officer", "specialization": "patrol", "is_on_duty": True, "park": "Chivero (Meikles) Recreational Park", "lat": -17.88, "lng": 30.55},
    {"name": "Privilege Gwaze", "badge_number": "ZKW-141", "email": "privilege.gwaze@zimparks.co.zw", "phone": "+263771000012", "rank": "trainee", "specialization": "patrol", "is_on_duty": True, "park": "Kariba", "lat": -16.52, "lng": 28.85},
]


def _random_point_in_park(center_lat, center_lng, spread=0.3):
    return center_lat + random.uniform(-spread, spread), center_lng + random.uniform(-spread, spread)


def seed_database():
    db = SessionLocal()
    rng = random.Random(20260903)

    print("Seeding database with Zimbabwe data...")

    for data in ZIMBABWE_PARKS:
        existing = db.query(ProtectedArea).filter(ProtectedArea.name == data["name"]).first()
        if not existing:
            db.add(ProtectedArea(
                name=data["name"],
                zone_type=data["zone_type"],
                risk_level=data["risk_level"],
                size_hectares=data["size_hectares"],
                description=data["description"],
                center_point=point_from_latlng(data["center_lat"], data["center_lng"]),
            ))
    db.commit()
    print(f"  Protected areas ready ({len(ZIMBABWE_PARKS)} parks)")

    for data in ZIMBABWE_SPECIES:
        existing = db.query(Species).filter(Species.name == data["name"]).first()
        if not existing:
            db.add(Species(**data))
    db.commit()
    print(f"  Species ready ({len(ZIMBABWE_SPECIES)} species)")

    areas = db.query(ProtectedArea).all()
    area_map = {a.name: a for a in areas}

    password_hash = get_password_hash(DEFAULT_PASSWORD)
    ranger_count = 0
    for data in RANGERS_DATA:
        existing = db.query(Ranger).filter(Ranger.badge_number == data["badge_number"]).first()
        if not existing:
            loc = point_from_latlng(data["lat"], data["lng"])
            assigned_area = area_map.get(data["park"])
            ranger_role = "admin" if data["email"] in ADMIN_USERS else "ranger"
            db.add(Ranger(
                name=data["name"],
                badge_number=data["badge_number"],
                email=data["email"],
                phone=data["phone"],
                role=ranger_role,
                rank=data["rank"],
                specialization=data["specialization"],
                is_active=True,
                is_on_duty=data["is_on_duty"],
                password_hash=password_hash,
                base_location=loc,
                current_location=loc,
                assigned_area_id=assigned_area.id if assigned_area else None,
            ))
            ranger_count += 1
        else:
            updated = False
            if not existing.password_hash:
                existing.password_hash = password_hash
                updated = True
            expected_role = "admin" if data["email"] in ADMIN_USERS else "ranger"
            if existing.role != expected_role:
                existing.role = expected_role
                updated = True
            assigned_area = area_map.get(data["park"])
            expected_area_id = assigned_area.id if assigned_area else None
            if expected_area_id and existing.assigned_area_id != expected_area_id:
                existing.assigned_area_id = expected_area_id
                updated = True
            if updated:
                ranger_count += 1
    db.commit()
    print(f"  Rangers ready ({ranger_count} added, default password: {DEFAULT_PASSWORD})")

    species_ids = [s.id for s in db.query(Species).all()]
    ranger_ids = [r.id for r in db.query(Ranger).all()]
    area_ids = [a.id for a in db.query(ProtectedArea).all()]

    if not species_ids or not ranger_ids or not area_ids:
        print("  Skipping incidents/reports/patrols — missing reference data.")
        db.close()
        return

    park_coords = {a.name: (a.center_lat if hasattr(a, 'center_lat') else -19.0, a.center_lng if hasattr(a, 'center_lng') else 29.5) for a in areas}
    for park_name, p in park_coords.items():
        if p[0] == -19.0:
            matching = next((pp for pp in ZIMBABWE_PARKS if pp["name"] == park_name), None)
            if matching:
                park_coords[park_name] = (matching["center_lat"], matching["center_lng"])

    INCIDENT_TYPES = ["poaching", "trespassing", "illegal_logging", "wildfire", "human_wildlife_conflict", "suspicious_activity"]
    SEVERITIES = ["low", "medium", "high", "critical"]
    PATROL_TYPES = ["routine", "intelligence_led", "rapid_response", "community_patrol"]
    STATUSES = ["planned", "active", "completed"]
    REPORT_TYPES = ["poaching", "suspicious_activity", "injured_animal", "fire", "illegal_activity"]

    existing_incidents = db.query(Incident).count()
    if existing_incidents < 5:
        for i in range(40):
            area = rng.choice(areas)
            lat, lng = _random_point_in_park(*park_coords.get(area.name, (-19.0, 29.5)))
            days_ago = rng.randint(0, 90)
            incident_type = rng.choice(INCIDENT_TYPES)
            severity = rng.choice(SEVERITIES)
            risk = rng.uniform(15, 98)
            if incident_type == "poaching":
                risk = max(risk, 60)
            if severity == "critical":
                risk = max(risk, 75)
            db.add(Incident(
                location=point_from_latlng(lat, lng),
                description=f"{incident_type.replace('_', ' ').title()} detected near {area.name} sector {rng.randint(1, 12)}",
                risk_score=round(risk, 1),
                incident_type=incident_type,
                severity=severity,
                species_id=rng.choice(species_ids),
                ranger_id=rng.choice(ranger_ids),
                protected_area_id=area.id,
                verified=rng.choice([True, True, True, False]),
                is_resolved=rng.choice([True, True, False, False]),
                timestamp=datetime.utcnow() - timedelta(days=days_ago, hours=rng.randint(0, 23)),
            ))
        db.commit()
        print(f"  Added 40 incidents")

    existing_reports = db.query(CommunityReport).count()
    if existing_reports < 5:
        for i in range(20):
            area = rng.choice(areas)
            lat, lng = _random_point_in_park(*park_coords.get(area.name, (-19.0, 29.5)), spread=0.15)
            db.add(CommunityReport(
                location=point_from_latlng(lat, lng),
                description=f"Community report: {rng.choice(REPORT_TYPES).replace('_', ' ')} sighting near {area.name}",
                reporter_phone=f"+26377{rng.randint(1000000, 9999999)}",
                is_anonymous=rng.choice([True, True, False]),
                report_type=rng.choice(REPORT_TYPES),
                risk_score=round(rng.uniform(10, 85), 1),
                status=rng.choice(["pending", "pending", "verified", "investigating", "resolved"]),
                assigned_ranger_id=rng.choice(ranger_ids),
                created_at=datetime.utcnow() - timedelta(days=rng.randint(0, 30), hours=rng.randint(0, 23)),
            ))
        db.commit()
        print(f"  Added 20 community reports")

    existing_patrols = db.query(Patrol).count()
    if existing_patrols < 5:
        for i in range(18):
            area = rng.choice(areas)
            lat, lng = park_coords.get(area.name, (-19.0, 29.5))
            route = []
            cur_lat, cur_lng = lat, lng
            for j in range(rng.randint(4, 8)):
                cur_lat += rng.uniform(-0.05, 0.05)
                cur_lng += rng.uniform(-0.05, 0.05)
                route.append({"lat": cur_lat, "lng": cur_lng})
            started_at = datetime.utcnow() - timedelta(days=rng.randint(0, 14), hours=rng.randint(4, 10))
            status = rng.choice(STATUSES)
            patrol_type = rng.choice(PATROL_TYPES)
            db.add(Patrol(
                route=linestring_from_coords(route),
                ranger_id=rng.choice(ranger_ids),
                protected_area_id=area.id,
                start_time=started_at,
                end_time=started_at + timedelta(hours=rng.randint(2, 8)) if status == "completed" else None,
                patrol_type=patrol_type,
                objectives=f"{patrol_type.replace('_', ' ').title()} patrol in {area.name} sector {rng.randint(1, 5)}",
                area_covered_km2=round(rng.uniform(8, 65), 1),
                status=status,
                notes=f"Patrol notes for {area.name} — {patrol_type}",
            ))
        db.commit()
        print(f"  Added 18 patrols")

    db.close()
    print("Database seeded successfully!")
    print(f"Login with: thandeka.ncube@zimparks.co.zw / {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    seed_database()
