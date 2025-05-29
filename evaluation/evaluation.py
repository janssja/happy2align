import os
import json
import random
from faker import Faker
from sklearn.feature_extraction.text import CountVectorizer

class SyntheticDataGenerator:
    """Generator voor synthetische dataset voor evaluatie van Happy 2 Align."""
    
    def __init__(self, output_dir="/home/ubuntu/happy2align/happy2align_app/src/evaluation/data"):
        """Initialiseer de generator."""
        self.output_dir = output_dir
        self.faker = Faker()
        
        # Zorg ervoor dat de output directory bestaat
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Definieer persona's
        self.personas = [
            {
                "name": "Beginner",
                "expertise_level": "laag",
                "vocabulary_richness": "laag",
                "query_complexity": "laag",
                "domain_knowledge": "beperkt"
            },
            {
                "name": "Gemiddelde gebruiker",
                "expertise_level": "gemiddeld",
                "vocabulary_richness": "gemiddeld",
                "query_complexity": "gemiddeld",
                "domain_knowledge": "basis"
            },
            {
                "name": "Expert",
                "expertise_level": "hoog",
                "vocabulary_richness": "hoog",
                "query_complexity": "hoog",
                "domain_knowledge": "uitgebreid"
            },
            {
                "name": "Domein specialist",
                "expertise_level": "zeer hoog",
                "vocabulary_richness": "zeer hoog",
                "query_complexity": "zeer hoog",
                "domain_knowledge": "diepgaand"
            }
        ]
        
        # Definieer domeinen
        self.domains = [
            "Software ontwikkeling",
            "Marketing",
            "Projectmanagement",
            "Financiën",
            "HR",
            "Onderwijs",
            "Gezondheidszorg",
            "Juridisch"
        ]
        
        # Voorbeeldvragen per domein en expertise niveau
        self.domain_questions = self._initialize_domain_questions()
    
    def _initialize_domain_questions(self):
        """Initialiseer voorbeeldvragen per domein en expertise niveau."""
        return {
            "Software ontwikkeling": {
                "laag": [
                    "Hoe maak ik een website?",
                    "Wat is programmeren?",
                    "Welke programmeertaal moet ik leren?"
                ],
                "gemiddeld": [
                    "Hoe zet ik een CI/CD pipeline op?",
                    "Wat zijn de beste practices voor API design?",
                    "Hoe implementeer ik authenticatie in mijn webapp?"
                ],
                "hoog": [
                    "Wat zijn de trade-offs tussen verschillende microservice architecturen?",
                    "Hoe optimaliseer ik de performance van mijn distributed database?",
                    "Welke design patterns zijn geschikt voor event-driven architecturen?"
                ]
            },
            "Marketing": {
                "laag": [
                    "Hoe maak ik een social media campagne?",
                    "Wat is SEO?",
                    "Hoe trek ik meer bezoekers naar mijn website?"
                ],
                "gemiddeld": [
                    "Hoe meet ik de ROI van mijn marketingcampagnes?",
                    "Welke KPI's zijn belangrijk voor content marketing?",
                    "Hoe zet ik een effectieve email marketing strategie op?"
                ],
                "hoog": [
                    "Hoe implementeer ik een omnichannel marketing strategie?",
                    "Welke attributiemodellen zijn het meest geschikt voor B2B marketing?",
                    "Hoe optimaliseer ik mijn marketing mix met behulp van econometrische modellen?"
                ]
            },
            # Andere domeinen volgen hetzelfde patroon
        }
    
    def generate_lexical_richness(self, level):
        """Genereer tekst met specifieke lexicale rijkdom."""
        if level == "laag":
            word_count = random.randint(5, 10)
            unique_words = random.randint(5, 8)
        elif level == "gemiddeld":
            word_count = random.randint(10, 20)
            unique_words = random.randint(8, 15)
        elif level == "hoog":
            word_count = random.randint(20, 30)
            unique_words = random.randint(15, 25)
        else:  # zeer hoog
            word_count = random.randint(30, 50)
            unique_words = random.randint(25, 40)
        
        # Genereer woorden
        words = [self.faker.word() for _ in range(unique_words)]
        
        # Herhaal woorden om aan word_count te komen
        text_words = []
        while len(text_words) < word_count:
            text_words.append(random.choice(words))
        
        # Shuffle en join
        random.shuffle(text_words)
        return " ".join(text_words)
    
    def measure_lexical_richness(self, text):
        """Meet de lexicale rijkdom van een tekst met CountVectorizer."""
        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform([text])
        
        # Bereken metrics
        total_words = X.sum()
        unique_words = len(vectorizer.get_feature_names_out())
        
        return {
            "total_words": int(total_words),
            "unique_words": unique_words,
            "ratio": unique_words / total_words if total_words > 0 else 0
        }
    
    def generate_query(self, persona, domain):
        """Genereer een query voor een specifieke persona en domein."""
        expertise_level = persona["expertise_level"]
        
        # Kies een basis vraag uit het domein en expertise niveau
        if domain in self.domain_questions and expertise_level in self.domain_questions[domain]:
            base_query = random.choice(self.domain_questions[domain][expertise_level])
        else:
            # Fallback als het domein of expertise niveau niet bestaat
            base_query = f"Ik wil meer weten over {domain}"
        
        # Voeg lexicale rijkdom toe op basis van persona
        richness_text = self.generate_lexical_richness(persona["vocabulary_richness"])
        
        # Combineer basis vraag met rijkdom
        if random.random() > 0.5:
            query = f"{base_query} {richness_text}"
        else:
            query = f"{richness_text}. {base_query}"
        
        return query
    
    def generate_dataset(self, num_samples=100):
        """Genereer een synthetische dataset."""
        dataset = []
        
        for _ in range(num_samples):
            # Kies willekeurige persona en domein
            persona = random.choice(self.personas)
            domain = random.choice(self.domains)
            
            # Genereer query
            query = self.generate_query(persona, domain)
            
            # Meet lexicale rijkdom
            lexical_metrics = self.measure_lexical_richness(query)
            
            # Voeg sample toe aan dataset
            sample = {
                "persona": persona["name"],
                "expertise_level": persona["expertise_level"],
                "domain": domain,
                "query": query,
                "lexical_metrics": lexical_metrics
            }
            
            dataset.append(sample)
        
        # Sla dataset op
        with open(os.path.join(self.output_dir, "synthetic_dataset.json"), "w") as f:
            json.dump(dataset, f, indent=2)
        
        return dataset

class Evaluator:
    """Evaluator voor Happy 2 Align."""
    
    def __init__(self, dataset_path="/home/ubuntu/happy2align/happy2align_app/src/evaluation/data/synthetic_dataset.json"):
        """Initialiseer de evaluator."""
        self.dataset_path = dataset_path
        self.dataset = self._load_dataset()
        
        # Definieer evaluatierubrieken
        self.rubrics = [
            "volledigheid_vereisten",
            "uitvoerbaarheid_workflows",
            "afstemming_gebruikersintent",
            "aanpassing_gebruikersexpertise",
            "efficientie_verfijningsproces"
        ]
    
    def _load_dataset(self):
        """Laad de dataset."""
        if os.path.exists(self.dataset_path):
            with open(self.dataset_path, "r") as f:
                return json.load(f)
        return []
    
    def evaluate_sample(self, sample, requirements, workflow):
        """Evalueer een sample met FM-jury simulatie."""
        # In een echte implementatie zou dit een call naar een FM-jury zijn
        # Voor deze demo simuleren we de evaluatie
        
        # Haal relevante informatie op
        expertise_level = sample["expertise_level"]
        domain = sample["domain"]
        
        # Simuleer scores op basis van expertise en domein
        scores = {}
        
        # Volledigheid vereisten (hoger voor experts)
        if expertise_level in ["hoog", "zeer hoog"]:
            scores["volledigheid_vereisten"] = random.uniform(7.0, 9.0)
        else:
            scores["volledigheid_vereisten"] = random.uniform(6.0, 8.0)
        
        # Uitvoerbaarheid workflows
        scores["uitvoerbaarheid_workflows"] = random.uniform(6.5, 9.5)
        
        # Afstemming gebruikersintent
        scores["afstemming_gebruikersintent"] = random.uniform(7.0, 9.0)
        
        # Aanpassing gebruikersexpertise (hoger als het systeem zich aanpast aan het niveau)
        if expertise_level == "laag":
            complexity_factor = self._measure_complexity(requirements, workflow)
            if complexity_factor < 0.3:  # Eenvoudige taal voor beginners
                scores["aanpassing_gebruikersexpertise"] = random.uniform(8.0, 9.5)
            else:
                scores["aanpassing_gebruikersexpertise"] = random.uniform(5.0, 7.0)
        else:
            complexity_factor = self._measure_complexity(requirements, workflow)
            if complexity_factor > 0.6 and expertise_level in ["hoog", "zeer hoog"]:
                scores["aanpassing_gebruikersexpertise"] = random.uniform(8.0, 9.5)
            else:
                scores["aanpassing_gebruikersexpertise"] = random.uniform(6.0, 8.0)
        
        # Efficiëntie verfijningsproces
        scores["efficientie_verfijningsproces"] = random.uniform(6.0, 9.0)
        
        return scores
    
    def _measure_complexity(self, requirements, workflow):
        """Meet de complexiteit van vereisten en workflow."""
        # Combineer tekst
        combined_text = " ".join(requirements + workflow)
        
        # Gebruik CountVectorizer voor lexicale analyse
        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform([combined_text])
        
        # Bereken metrics
        total_words = X.sum()
        unique_words = len(vectorizer.get_feature_names_out())
        avg_word_length = sum(len(word) for word in combined_text.split()) / len(combined_text.split()) if combined_text else 0
        
        # Normaliseer tot een score tussen 0 en 1
        complexity_score = (
            (unique_words / total_words if total_words > 0 else 0) * 0.5 +
            (min(avg_word_length / 10, 1.0) * 0.5)
        )
        
        return complexity_score
    
    def run_evaluation(self, model_name="Happy2Align"):
        """Voer evaluatie uit op de volledige dataset."""
        results = {
            "model": model_name,
            "samples": [],
            "average_scores": {rubric: 0.0 for rubric in self.rubrics}
        }
        
        for sample in self.dataset:
            # Simuleer het genereren van vereisten en workflow
            # In een echte implementatie zou dit het model aanroepen
            requirements = [
                f"Het systeem moet {domain.lower()} functionaliteit bieden",
                f"Gebruikers moeten {domain.lower()} taken kunnen uitvoeren",
                f"Het systeem moet rapportages over {domain.lower()} kunnen genereren"
            ]
            
            workflow = [
                f"1. Analyseer de huidige {domain.lower()} processen",
                f"2. Identificeer verbeterpunten in {domain.lower()}",
                f"3. Implementeer nieuwe {domain.lower()} functionaliteit",
                f"4. Test de {domain.lower()} functionaliteit",
                f"5. Evalueer de resultaten"
            ]
            
            # Evalueer sample
            scores = self.evaluate_sample(sample, requirements, workflow)
            
            # Voeg resultaten toe
            sample_result = {
                "sample": sample,
                "requirements": requirements,
                "workflow": workflow,
                "scores": scores
            }
            
            results["samples"].append(sample_result)
            
            # Update gemiddelde scores
            for rubric in self.rubrics:
                results["average_scores"][rubric] += scores[rubric]
        
        # Bereken gemiddelden
        num_samples = len(self.dataset)
        if num_samples > 0:
            for rubric in self.rubrics:
                results["average_scores"][rubric] /= num_samples
        
        # Bereken totaalscore
        results["total_score"] = sum(results["average_scores"].values()) / len(self.rubrics)
        
        # Sla resultaten op
        output_path = os.path.join(os.path.dirname(self.dataset_path), f"evaluation_results_{model_name}.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        return results

def generate_and_evaluate():
    """Genereer dataset en voer evaluatie uit."""
    # Maak directory structuur
    eval_dir = "/home/ubuntu/happy2align/happy2align_app/src/evaluation"
    data_dir = os.path.join(eval_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Genereer dataset
    generator = SyntheticDataGenerator(output_dir=data_dir)
    dataset = generator.generate_dataset(num_samples=50)
    
    # Voer evaluatie uit
    evaluator = Evaluator(dataset_path=os.path.join(data_dir, "synthetic_dataset.json"))
    results = evaluator.run_evaluation()
    
    # Voer baseline evaluatie uit voor vergelijking
    baseline_results = evaluator.run_evaluation(model_name="Baseline")
    
    return {
        "dataset_size": len(dataset),
        "happy2align_score": results["total_score"],
        "baseline_score": baseline_results["total_score"]
    }

if __name__ == "__main__":
    generate_and_evaluate()
