## Restaurants create
curl -H "Content-Type: application/json" \
  --request POST \
  --data '{"name":"coolway", "tables": [{"id": 1, "cost": 100}], "menu_id": 1}' \
  http://localhost:5000
  
 
 ## Booking request
 curl -H "Content-Type: application/json" \
  --request POST \
  --data '{"restaurant_id":1, "user_id": 1, "menu_id": 1, "items": "pizza", "table_id": 1}' \
  http://localhost:5001