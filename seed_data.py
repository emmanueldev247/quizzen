"""Seed data for category"""

from app import create_app, db
from app.models import Category

app = create_app()

# List of categories
categories = [
    "General Knowledge",
    "Science and Technology",
    "History",
    "Geography",
    "Literature",
    "Mathematics",
    "Sports",
    "Music",
    "Movies and TV Shows",
    "Art and Culture",
    "Programming and Computer Science",
    "Health and Fitness",
    "Business and Economics",
    "Languages",
    "Travel and Adventure",
    "Others"
]

with app.app_context():
    for category_name in categories:
        existing_cat = Category.query.filter_by(name=category_name).first()
        if not existing_cat:
            category = Category(name=category_name)
            db.session.add(category)

    db.session.commit()

print("Categories added successfully!")
