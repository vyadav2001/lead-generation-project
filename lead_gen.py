import requests
import json
from bs4 import BeautifulSoup
from openai import OpenAI
import pandas as pd
import random
import re


APOLLO_API_KEY = "VQ3wlo_n9tuBI6Rh-49vqA"  ## Just for the reference, later to be added in .env file


client = OpenAI(
    base_url="http://localhost:11434/v1",  
    api_key="ollama"  
)

def search_leads(criteria):
    """Search for leads using Apollo.io API (fallback to mocks if API fails)."""
    url = "https://api.apollo.io/v1/organizations/search"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    params = {
        "api_key": APOLLO_API_KEY,
        "q": {
            "employees": {"$gte": 50, "$lte": 200}, 
            "industry": "software", 
            "country": "United States",  
            "city": "New York"
        },
        "per_page": 10  
    }
    try:
        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        data = response.json()
        if data.get("organizations"):
            leads = []
            for org in data["organizations"][:10]:  
                lead = {
                    "name": org.get("name", "Unknown Company"),
                    "website": org.get("website_url", f"https://{org.get('domain', 'example.com')}"),
                    "employees": str(org.get("number_of_employees", "N/A"))
                }
                leads.append(lead)
                print(f"Found lead via Apollo.io: {lead}")
            print(f"Using {len(leads)} leads from Apollo.io.")
            return leads
        else:
            print("No leads found with Apollo.io; using mock data.")
            raise Exception("No Apollo data")

    except requests.exceptions.RequestException as e:
        print(f"API Error with Apollo.io: {e}. Falling back to mock data.")

        mock_leads = [
            {"name": "Zomato", "website": "https://www.zomato.com", "employees": "150"},
            {"name": "Zepto", "website": "https://www.zepto.com", "employees": "120"},
            {"name": "Swiggy", "website": "https://www.swiggy.com", "employees": "180"},
            {"name": "Blinkit", "website": "https://www.blinkit.com", "employees": "90"},
            {"name": "Domino’s India", "website": "https://www.dominos.co.in", "employees": "130"}
        ]
        return mock_leads
    

def scrape_insights(website):
    """Extract 2-3 key insights from a company website (with fallback)."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(website, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        insights = []

        about_section = soup.find('div', class_=['about', 'company', 'overview']) or soup.find('section', id=['about', 'company'])
        if about_section:
            text = about_section.get_text().lower()
            if 'software' in text or 'development' in text:
                insights.append("Company focuses on software development.")
            if 'team' in text and any(num in text for num in ['100', '200', '50']):
                insights.append("They have a team of 100+ developers.")


        services_section = soup.find('div', class_=['services', 'products']) or soup.find('section', id=['services', 'products'])
        if services_section:
            text = services_section.get_text().lower()
            if 'it' in text or 'infrastructure' in text:
                insights.append("Recent content on IT infrastructure needs.")

        if not insights:
            insights = [
                "Focuses on innovative software solutions.",
                "Employs a dynamic team of developers.",
                "Discusses hardware needs in recent updates."
            ]
        return insights[:3]

    except requests.exceptions.RequestException as e:
        print(f"Scraping error for {website}: {e}. Using fallback insights.")
        return [
            "Focuses on innovative software solutions.",
            "Employs a dynamic team of developers.",
            "Discusses hardware needs in recent updates."
        ]
    
def validate_email(email):
    """Check if an email is valid using regex."""
    if not email:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    match = re.match(pattern, email)
    return bool(match)

def find_contacts(website):
    """Find emails and phones from website text."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(website, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text() 


        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)

        phone_pattern = r'[\+]?[9][1]?[6-9]\d{9}' 
        phones = re.findall(phone_pattern, page_text)


        valid_emails = [email for email in emails if validate_email(email)]

        return {
            "emails": valid_emails[:2],  
            "phones": phones[:2]
        }
    except requests.exceptions.RequestException as e:
        print(f"Contact finding error for {website}: {e}. No contacts found.")
        return {"emails": [], "phones": []}


def generate_message(company_data):
    """Generate a personalized outreach message using Ollama (local LLM)."""
    prompt = f"""You are a founder of a hardware computer store specializing in custom PCs and servers. Write a concise, professional B2B outreach email (2-3 sentences) to the team at {company_data['name']}. Reference their specific business insights: {', '.join(company_data['insights'])}. Highlight how our hardware solutions (e.g., high-performance computers for development teams) can address their needs, and end with a call-to-action to schedule a quick call. Do NOT include a closing signature (e.g., 'Best regards' or name); I will add it."""
    try:
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        message = response.choices[0].message.content.strip()

        if not message.endswith(("Best regards", "Sincerely", "Thanks")):
            message += "\n\nBest regards,\n[Your Name]\nFounder, Custom Hardware Solutions"
        return message
    except Exception as e:
        print(f"LLM Error for {company_data['name']}: {e}. Using fallback.")
        return f"Hi [Contact], As a hardware store founder, I noticed {company_data['name']} could benefit from our custom computers tailored to your software needs. Let's schedule a call to discuss.\n\nBest regards,\n[Your Name]"
    
def score_lead(lead, index):
    """Score lead based on employees, insights, and a random factor (0-100, unique per lead)."""
    score = 50 
    insights = " ".join(lead.get("insights", [])).lower()
    

    try:
        employees = int(lead.get("employees", "0"))
        if employees >= 150:
            score += 30
        elif employees >= 100:
            score += 20 
        elif employees >= 50:
            score += 10 
    except ValueError:
        pass 

    if "hardware" in insights:
        score += 15
    if "development" in insights or "developers" in insights:
        score += 10
    if "infrastructure" in insights:
        score += 10

    random_bonus = random.randint(0, 10) 
    score += random_bonus


    score += index * 2 

    return min(max(score, 0), 100) 

def output_leads(leads):
    """Output enriched leads to console, JSON, and CSV."""
    print("\nGenerated Leads with Personalized Messages:")
    enriched_leads = []
    for index, lead in enumerate(leads[:5]): 
        print(f"\n--- Enriching {lead['name']} ---")
        lead["insights"] = scrape_insights(lead["website"])
        lead["contacts"] = find_contacts(lead["website"])  
        
        if lead["contacts"]["emails"]:
            lead["valid_emails"] = [email for email in lead["contacts"]["emails"] if validate_email(email)]
        else:
            lead["valid_emails"] = []
        lead["message"] = generate_message(lead)
        lead["score"] = score_lead(lead, index)
        enriched_leads.append(lead)
        print(f"Company: {lead['name']}")
        print(f"Website: {lead['website']}")
        print(f"Employees: {lead['employees']}")
        print(f"Insights: {lead['insights']}")
        print(f"Contacts: Emails - {lead['valid_emails']}, Phones - {lead['contacts']['phones']}")
        print(f"Score: {lead['score']}")
        print(f"Personalized Message:\n{lead['message']}\n")


    with open("leads.json", "w") as f:
        json.dump(enriched_leads, f, indent=4)


    df = pd.DataFrame(enriched_leads)
    df.to_csv("leads.csv", index=False)
    print("Enriched leads saved to leads.json and leads.csv")

def generate_dashboard(leads):
    """Generate a simple HTML dashboard."""
    html = """
    <html><body><h2>Lead Generation Dashboard</h2><table border="1">
    <tr><th>Company</th><th>Website</th><th>Employees</th><th>Score</th><th>Message</th></tr>
    """
    for lead in leads[:5]:

        message_html = lead['message'].replace('\n', '<br>')
        html += f"<tr><td>{lead['name']}</td><td><a href='{lead['website']}'>{lead['website']}</a></td><td>{lead['employees']}</td><td>{lead['score']}</td><td>{message_html}</td></tr>"
    html += "</table></body></html>"
    with open("dashboard.html", "w") as f:
        f.write(html)
    print("Dashboard saved as dashboard.html")

def main():
    """Main pipeline: Search, enrich, generate, output."""
    criteria = {"size_range": "50-200", "keywords": "software", "location": "New York"} 
    print("Starting Lead Generation Pipeline...")
    leads = search_leads(criteria)
    output_leads(leads)
    generate_dashboard(leads)
    print("\nDemo complete! Check leads.json, leads.csv, and dashboard.html for output.")

if __name__ == "__main__":
    main()

