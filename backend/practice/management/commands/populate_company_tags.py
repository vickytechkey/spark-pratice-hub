import random
from django.core.management.base import BaseCommand
from practice.models import Problem, Challenge

class Command(BaseCommand):
    help = 'Populates company tags for problems and seeds custom challenges with badges'

    def handle(self, *args, **options):
        companies_list = [
            "Google", "Meta", "Amazon", "Microsoft", "Apple", "Netflix", "Uber", 
            "Airbnb", "LinkedIn", "Adobe", "Salesforce", "Databricks", "Snowflake", 
            "NVIDIA", "Oracle", "Atlassian", "Stripe", "Bloomberg", "Walmart Global Tech", 
            "Goldman Sachs", "JPMorgan Chase", "Cisco", "Intel", "Qualcomm", "PayPal", 
            "Expedia", "Booking.com", "Spotify"
        ]
        
        frequencies = ["Frequently Asked", "Occasionally Asked", "Rarely Asked"]
        
        # 1. Populate Company Tags on all problems
        problems = Problem.objects.all()
        if not problems.exists():
            self.stdout.write(self.style.WARNING("No problems found in the database. Please run problem generation first."))
            return
            
        random.seed(123)  # Stable random assignments
        for prob in problems:
            num_companies = random.randint(1, 4)
            chosen_companies = random.sample(companies_list, num_companies)
            companies_data = []
            for company in chosen_companies:
                freq = random.choice(frequencies)
                companies_data.append({
                    "company": company,
                    "frequency": freq
                })
            prob.companies = companies_data
            prob.save()
            
        self.stdout.write(self.style.SUCCESS(f"Successfully populated company tags for {problems.count()} problems."))
        
        # 2. Seed Custom Challenges
        challenges_definitions = [
            {
                "id": "ch_data_cleanser",
                "name": "Data Cleanser Challenge",
                "description": "Master the art of cleaning dirty datasets and dealing with missing data.",
                "badge_name": "Data Cleanser Master",
                "badge_icon": "ShieldAlert",
                "categories": ["Data Cleaning & Null Handling"]
            },
            {
                "id": "ch_window_wizard",
                "name": "Window Wizard Challenge",
                "description": "Unlock advanced analytical capabilities using PySpark window specs.",
                "badge_name": "Window Wizard",
                "badge_icon": "Award",
                "categories": ["Window Functions"]
            },
            {
                "id": "ch_join_specialist",
                "name": "Join Specialist Challenge",
                "description": "Understand inner, outer, left, right and broadcast joins in Spark.",
                "badge_name": "Join Specialist",
                "badge_icon": "Compass",
                "categories": ["Joins"]
            },
            {
                "id": "ch_performance_guru",
                "name": "Performance Guru Challenge",
                "description": "Tune partitioning, broadcast thresholds, and optimize queries.",
                "badge_name": "Performance Guru",
                "badge_icon": "Trophy",
                "categories": ["Performance & Optimization"]
            },
            {
                "id": "ch_array_explorer",
                "name": "Array Explorer Challenge",
                "description": "Solve complex problems involving array transformations and map operations.",
                "badge_name": "Array Explorer",
                "badge_icon": "Star",
                "categories": ["Array & Map Operations"]
            }
        ]
        
        for c_def in challenges_definitions:
            challenge, created = Challenge.objects.get_or_create(
                id=c_def["id"],
                defaults={
                    "name": c_def["name"],
                    "description": c_def["description"],
                    "badge_name": c_def["badge_name"],
                    "badge_icon": c_def["badge_icon"]
                }
            )
            
            # Select 3-5 problems from specified categories
            probs_for_challenge = Problem.objects.filter(category__in=c_def["categories"])
            # Let's take the first 4 problems as the challenge problems
            subset = probs_for_challenge[:4]
            challenge.problems.set(subset)
            challenge.save()
            
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} challenge '{challenge.name}' with {len(subset)} problems."))
            
        self.stdout.write(self.style.SUCCESS("Custom challenges and badges successfully seeded."))
