from fastapi import APIRouter, HTTPException
from ..schemas.order import OrderCreate, Order
from ..services.order_service import OrderService
import logging

router = APIRouter(prefix="/orders", tags=["orders"])
order_service = OrderService()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Order)
async def create_order(order: OrderCreate):
    try:
        logger.info(f"Creating order with data: {order}")
        order_id = await order_service.create_order(order)
        return await order_service.get_order(order_id)
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=list[Order])
async def get_orders():
    try:
        return await order_service.get_all_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: int):
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order 