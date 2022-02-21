from django.conf import settings
from django.core.paginator import Paginator


def get_page_obj(posts: list,
                 page_number: int,
                 paginator_count_of_posts:
                 int = settings.COUNT_OF_POSTS_DEFAULT
                 ) -> int:
    paginator = Paginator(posts, paginator_count_of_posts)
    page_obj = paginator.get_page(page_number)
    return page_obj
