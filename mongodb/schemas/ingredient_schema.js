const ingredientSchema = {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["id", "name", "nutrition_per_100"],
            properties: {
                id: {bsonType: "string"},
                name: {bsonType: "string"},
                nutrition_per_100: {
                    bsonType: "object",
                    required: ["kcal", "carbs", "fat", "protein"],
                    properties: {
                        kcal:    {bsonType: "double", minimum: 0},
                        carbs:   {bsonType: "double", minimum: 0},
                        fat:     {bsonType: "double", minimum: 0},
                        protein: {bsonType: "double", minimum: 0}
                    }
                }
            }
        }
    }
};
