import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vitrina.settings")
django.setup()

from cms.api import create_page
from cms.models import Page
from django.contrib.sites.models import Site


PAGES = [
    {
        "title": "Duomenų ištekliai",
        "slug": "datasets",
        "is_home": True,
        "in_navigation": True,
    },
    {
        "title": "Naujienos",
        "slug": "naujienos",
        "in_navigation": True,
    },
    {
        "title": "Mokymai",
        "slug": "mokymai",
        "in_navigation": True,
    },
]

LANGUAGE = "lt"
TEMPLATE = "INHERIT"


def run():
    site = Site.objects.get_current()
    print(f"Creating pages on site: {site}")

    home_page = None

    for page_def in PAGES:
        title = page_def["title"]
        slug = page_def.get("slug")
        is_home = page_def.get("is_home", False)
        in_navigation = page_def.get("in_navigation", False)

        page = create_page(
            title=title,
            template=TEMPLATE,
            language=LANGUAGE,
            slug=slug,
            in_navigation=in_navigation,
            site=site,
            published=True,
        )

        if is_home:
            page.set_as_homepage()
            home_page = page

        print(f"  Created: '{title}' (slug={slug!r}, is_home={is_home})")

    print(f"\nDone. {len(PAGES)} pages created.")
    if home_page:
        print(f"Homepage set to: '{home_page.get_title()}'")


if __name__ == "__main__":
    run()
