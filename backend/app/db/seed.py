from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.all_models import ExpenseCategory

DEFAULT_CATEGORIES = [
    "Food & Groceries",
    "Transportation",
    "Education",
    "Personal Care",
    "Health & Medicine",
    "Mobile Recharge",
    "Shopping",
    "Entertainment",
    "Household Items",
    "Snacks & Drinks",
    "Social & Gifts",
    "Other Expenses",
]


def seed_default_categories(db: Session) -> None:
    existing = set(
        db.scalars(
            select(ExpenseCategory.name).where(ExpenseCategory.is_default.is_(True))
        ).all()
    )
    for name in DEFAULT_CATEGORIES:
        if name not in existing:
            db.add(
                ExpenseCategory(
                    user_id=None,
                    name=name,
                    category_type="EXPENSE",
                    is_default=True,
                )
            )
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_default_categories(session)
        count = len(
            session.scalars(
                select(ExpenseCategory).where(ExpenseCategory.is_default.is_(True))
            ).all()
        )
        print(f"Seeded successfully! Total default categories in DB: {count}")
