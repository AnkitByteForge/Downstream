from __future__ import annotations

from infrastructure.persistence.db import SessionLocal
from seed.meridian_tower_commercial import seed


def main() -> None:
    session = SessionLocal()
    try:
        result = seed(session)
        session.commit()
        print("Seed complete:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
