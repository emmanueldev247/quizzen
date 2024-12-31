from app import db
from app.models import Category

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
    "Travel and Adventure"
]

# Add categories to the database
for category_name in categories:
    category = Category(name=category_name)
    db.session.add(category)

# Commit changes
db.session.commit()

print("Categories added successfully!")