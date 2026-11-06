from django.urls import path

from . import auth_views, views

urlpatterns = [
    # Open to logged-out visitors: only what the login page needs (S23).
    path("auth/config", auth_views.config),
    path("auth/me", auth_views.me),
    path("auth/google", auth_views.google_login),
    path("auth/dev-login", auth_views.dev_login),
    path("auth/logout", auth_views.logout_view),
    # Everything below needs login.
    path("items", views.items),
    path("items/<int:pk>/claim", views.claim_item),
    path("reports", views.reports),
    path("reports/<int:pk>", views.report_detail),
    path("claims", views.my_claims),
    path("notifications", views.notifications),
    path("notifications/read", views.notifications_read),
    # Admin only (S3). Every route under admin/ must use IsAdmin.
    path("admin/items", views.admin_items),
    path("admin/items/<int:pk>", views.admin_item_detail),
    path("admin/items/<int:pk>/photo", views.admin_item_photo),
    path("admin/items/<int:pk>/link", views.admin_item_link),
    path("admin/items/<int:pk>/handover", views.admin_item_handover),
    path("admin/claims/pending", views.admin_pending_claims),
    path("admin/claims/<int:pk>/approve", views.admin_claim_approve),
    path("admin/claims/<int:pk>/reject", views.admin_claim_reject),
    path("admin/handovers", views.admin_handovers),
]
