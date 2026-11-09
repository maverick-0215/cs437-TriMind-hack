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
    path("reports", views.reports),
    path("reports/<int:pk>", views.report_detail),
    path("claims", views.my_claims),
    path("items", views.items),
    path("notifications", views.notifications),
    path("notifications/read", views.notifications_read),
    # Admin only (S3). Every route under admin/ must use IsAdmin.
    path("admin/items", views.admin_items),
    path("admin/items/<int:pk>", views.admin_item_detail),
    path("admin/items/<int:pk>/photo", views.admin_item_photo),
    path("admin/items/<int:pk>/approve", views.admin_item_approve),
    path("admin/items/<int:pk>/handover", views.admin_item_handover),
    path("admin/pickups", views.admin_pickups),
    path("admin/claims/<int:pk>/cancel", views.admin_claim_cancel),
    path("admin/handovers", views.admin_handovers),
    path("admin/admins", views.admin_admins),
    path("admin/admins/<int:pk>/remove", views.admin_admin_remove),
]
