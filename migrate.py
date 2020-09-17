""" Purpose: Make it fast and easy to migrate dev database.

Compares two schemas

1. Temporary, random named and empty database based on the current
declarative models in the dev codebase.
2. Current dev schema.

Prints a migration script and offers to run it, if there is a diff.

"""

import os

import typer
from migra import Migration


def sync(DB_URL: str = "postgresql://orflaedi:@localhost/orflaedi"):
    from sqlbag import S, temporary_database as temporary_db

    with temporary_db() as TEMP_DB_URL:
        os.environ["DATABASE_URL"] = TEMP_DB_URL
        from orflaedi.database import engine, Base
        from orflaedi.models import Model, Retailer, VehicleClassEnum, TagEnum

        Base.metadata.create_all(engine)

        with S(DB_URL) as s_current, S(TEMP_DB_URL) as s_target:
            m = Migration(s_current, s_target)
            m.set_safety(False)
            m.add_all_changes()

            if m.statements:
                print("THE FOLLOWING CHANGES ARE PENDING:", end="\n\n")
                print(m.sql)
                print()
                if input("Apply these changes?") == "yes":
                    print("Applying...")
                    m.apply()
                else:
                    print("Not applying.")
            else:
                print("Already synced.")


if __name__ == "__main__":
    typer.run(sync)
