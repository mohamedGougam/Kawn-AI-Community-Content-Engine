"""Generate the mobile developer integration guide PDF."""

from pathlib import Path

from fpdf import FPDF

OUTPUT = Path(__file__).parent / "Kawn-Mobile-Developer-Integration-Guide.pdf"


class GuidePDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "Kawn AI Content Engine - Mobile Developer Guide", align="R", new_x="LMARGIN", new_y="NEXT")

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def title_page(self):
        self.add_page()
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(30, 41, 59)
        self.ln(40)
        self.multi_cell(0, 12, "Kawn AI Content Engine\nMobile Developer Integration Guide", align="C")
        self.ln(10)
        self.set_font("Helvetica", "", 12)
        self.set_text_color(71, 85, 105)
        self.multi_cell(
            0,
            7,
            "How to get AI-generated, theme-based posts into Kawn community feeds automatically.",
            align="C",
        )
        self.ln(20)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, "Kawn Platform", align="C")

    def h1(self, text: str):
        self.ln(4)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 41, 59)
        self.multi_cell(self.epw, 9, text)
        self.ln(2)

    def h2(self, text: str):
        self.ln(2)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(51, 65, 85)
        self.multi_cell(self.epw, 8, text)
        self.ln(1)

    def h3(self, text: str):
        self.ln(1)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(71, 85, 105)
        self.multi_cell(self.epw, 7, text)

    def body(self, text: str):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(self.epw, 6, text)
        self.ln(1)

    def bullet(self, text: str):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(self.epw, 6, f"- {text}")

    def code_block(self, text: str):
        self.set_font("Courier", "", 8.5)
        self.set_fill_color(248, 250, 252)
        self.set_text_color(15, 23, 42)
        for line in text.strip().splitlines():
            self.set_x(self.l_margin)
            self.multi_cell(self.epw, 5, f"  {line}", fill=True)
        self.ln(2)


def build_pdf() -> None:
    pdf = GuidePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.title_page()

    pdf.add_page()
    pdf.h1("The simple version")
    pdf.body(
        "The Content Engine is a separate system. It knows each community's theme (football, cricket, AI, etc.), "
        "reads related news, writes posts with AI, checks them for safety, and when ready sends them to the Kawn app "
        "through an API that you build."
    )
    pdf.body(
        "The Flutter app does NOT talk to the Content Engine directly. Your developer builds one API on the Kawn "
        "backend. The Content Engine calls it when a post is ready."
    )
    pdf.body("Content Engine = the writer | Kawn backend = the door into the app | Flutter app = shows posts normally")

    pdf.h1("What 'theme wise' means")
    pdf.body(
        "You do not need to write AI logic in the app. When a community is registered in the Content Engine, send its "
        "theme info. The engine uses it to generate posts that fit each community."
    )
    pdf.h3("Theme fields to send")
    pdf.bullet("category - main topic (e.g. football)")
    pdf.bullet("tags - specific theme (e.g. france, les-bleus)")
    pdf.bullet("blocked_topics - topics to avoid (e.g. cricket)")
    pdf.bullet("country - local relevance (e.g. France)")
    pdf.bullet("preferred_tone - how posts should sound (e.g. passionate)")
    pdf.bullet("language - post language (e.g. en or fr)")
    pdf.body("France Fans gets France football content. India Cricket gets cricket content. And so on.")
    pdf.h3("Post style by time of day (UTC)")
    pdf.bullet("Morning (~8am): morning update")
    pdf.bullet("Midday (~11am): news discussion")
    pdf.bullet("Afternoon (~2pm): poll")
    pdf.bullet("Evening (~6pm): news discussion")
    pdf.bullet("Night (~9pm): evening recap")

    pdf.h1("Your job in 3 steps")

    pdf.h2("Step 1 - Register every Kawn community in the Content Engine")
    pdf.body("When a community is created or updated in Kawn, the backend should also tell the Content Engine.")
    pdf.body("Call:")
    pdf.code_block("POST https://YOUR-CONTENT-ENGINE.onrender.com/api/communities")
    pdf.body("Example body:")
    pdf.code_block(
        """{
  "name": "France National Team Fans",
  "description": "Fans discussing Les Bleus",
  "category": "football",
  "tags": ["france", "football", "national-team"],
  "blocked_topics": ["cricket"],
  "country": "France",
  "preferred_tone": "passionate",
  "language": "en",
  "kawn_community_id": "12345",
  "posts_per_day": 2,
  "is_active": true
}"""
    )
    pdf.body(
        "Important: kawn_community_id is the real community ID from your Kawn database. The engine needs it to know "
        "where to publish."
    )
    pdf.bullet("PUT /api/communities/{engine_id} when community details change")
    pdf.bullet("Set is_active to false when a community is disabled")

    pdf.h2("Step 2 - Build ONE API endpoint on the Kawn backend (main work)")
    pdf.body("The Content Engine will call your API to create a post inside a community.")
    pdf.code_block(
        """POST /api/v1/communities/{community_id}/posts
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json"""
    )
    pdf.body("Body the engine sends:")
    pdf.code_block(
        """{
  "title": "France has announced its latest squad",
  "body": "Which player are you most excited to watch?",
  "post_type": "news_discussion",
  "tone": "passionate",
  "hashtags": ["france", "football"],
  "poll_options": null,
  "source_engine_post_id": "uuid-from-content-engine"
}"""
    )
    pdf.body("For polls, post_type will be poll and poll_options will be an array.")
    pdf.h3("Your API must:")
    pdf.bullet("Check the API key (Bearer token)")
    pdf.bullet("Find the community by community_id")
    pdf.bullet("Create a normal community post in Kawn DB")
    pdf.bullet('Use a system/bot author (e.g. Kawn Community) - not a real user')
    pdf.bullet('Return the new post ID as JSON: {"id": "your-kawn-post-id"}')
    pdf.bullet("If source_engine_post_id already exists, return the existing post ID (no duplicates)")

    pdf.h2("Step 3 - Give the Content Engine your API details")
    pdf.body("Set these environment variables on the Content Engine (Render):")
    pdf.bullet("KAWN_APP_API_URL = your Kawn backend base URL")
    pdf.bullet("KAWN_APP_API_KEY = the secret key your endpoint checks")
    pdf.bullet("KAWN_AUTO_PUBLISH = true (posts go live automatically)")
    pdf.body("Flow: AI writes post -> safety check -> approved -> sent to Kawn API -> shows in app feed")

    pdf.add_page()
    pdf.h1("What the Flutter app needs to do")
    pdf.bullet("Keep loading the community feed from the Kawn backend as today")
    pdf.bullet('Render poll posts if post_type is poll')
    pdf.bullet('Optionally show a badge like Community host or AI post')
    pdf.bullet("No direct calls to the Content Engine from the app")

    pdf.h1("Daily posting")
    pdf.body(
        "The Content Engine scheduler generates posts on a schedule. For about 2 posts per day per community, set "
        "posts_per_day to 2 when registering the community."
    )
    pdf.body(
        "Registering communities with the right theme fields is enough to get themed daily content flowing. Stricter "
        "timing (e.g. exactly 8am and 8pm) is a Content Engine scheduler setting, not mobile work."
    )

    pdf.h1("Checklist")
    pdf.bullet("1. Build POST /api/v1/communities/{id}/posts (Backend)")
    pdf.bullet("2. Add API key auth - Bearer token (Backend)")
    pdf.bullet("3. Store source_engine_post_id to avoid duplicates (Backend)")
    pdf.bullet("4. Sync communities to Content Engine with kawn_community_id (Backend)")
    pdf.bullet("5. Share API URL and key with Content Engine team (You / backend)")
    pdf.bullet("6. Show posts normally in Flutter feed (Mobile)")
    pdf.bullet("7. Support poll UI when post_type is poll (Mobile)")

    pdf.h1("How to test")
    pdf.bullet("Create a test community in Kawn")
    pdf.bullet("Sync it to Content Engine with category, tags, and kawn_community_id")
    pdf.bullet("In Content Engine admin, manually generate a post for that community")
    pdf.bullet("Confirm it appears as Approved")
    pdf.bullet("Publish it (or turn on KAWN_AUTO_PUBLISH)")
    pdf.bullet("Check the post shows up in the Kawn app community feed")
    pdf.body("If publishing fails, check Kawn backend logs. The engine calls your API and expects a post ID back.")

    pdf.h1("One sentence summary")
    pdf.body(
        "Register each Kawn community in the Content Engine with its theme info and kawn_community_id, build one "
        "secure API endpoint that accepts posts into community feeds, and the engine will automatically publish "
        "themed daily content into the right communities."
    )

    pdf.output(OUTPUT)
    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
