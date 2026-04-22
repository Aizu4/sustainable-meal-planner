db = db.getSiblingDB(process.env.DB_NAME);

load('/docker-entrypoint-initdb.d/schemas/ingredient_schema.js');

db.createCollection('ingredients', ingredientSchema);
db.createCollection('recipes'); 

db.createUser({
  user: process.env.READWRITE_USERNAME,
  pwd: process.env.READWRITE_PASSWORD,
  roles: [
    { role: "readWrite", db: process.env.DB_NAME } 
  ]
});

db.createUser({
  user: process.env.READONLY_USERNAME,
  pwd: process.env.READONLY_PASSWORD,
  roles: [
    { role: "read", db: process.env.DB_NAME } 
  ]
});

