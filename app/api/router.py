from fastapi import APIRouter

from app.api.routes import admin, auth, customers, offers, orders, restaurants, users, wallet

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(customers.router)
api_router.include_router(restaurants.router)
api_router.include_router(offers.router)
api_router.include_router(orders.router)
api_router.include_router(admin.router)
api_router.include_router(wallet.router)
