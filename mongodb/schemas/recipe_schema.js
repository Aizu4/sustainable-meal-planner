const recipeSchema = {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["id", "name", "ingredients"],
            properties: {
                id: {bsonType: "string"},
                name: {bsonType: "string"},
                servings: {bsonType: "int", minimum: 1},
                image_url: {bsonType: "string"},
                source_url: {bsonType: "string"},
                cooking_time: {bsonType: "int", minimum: 0},
                is_vegan: {bsonType: "bool"},
                is_gluten_free: {bsonType: "bool"},
                allergens: {
                    bsonType: "array",
                    items: {bsonType: "int"},
                    uniqueItems: true
                },
                scraped_at: {bsonType: "string"},
                steps: {
                    bsonType: "array",
                    items: {bsonType: "string"}
                },
                nutrition: {
                    bsonType: "object",
                    required: ["kcal", "macro"],
                    properties: {
                        kcal: {bsonType: "double", minimum: 0},
                        macro: {
                            bsonType: "object",
                            required: ["carbs", "protein", "fat"],
                            properties: {
                                carbs: {bsonType: "double", minimum: 0},
                                protein: {bsonType: "double", minimum: 0},
                                fat: {bsonType: "double", minimum: 0},
                                fiber: {bsonType: "double", minimum: 0},
                                sugar: {bsonType: "double", minimum: 0}
                            }
                        }
                    }
                },
                ingredients: {
                    bsonType: "array",
                    minItems: 1,
                    items: {
                        bsonType: "object",
                        required: ["id", "name", "quantity"],
                        properties: {
                            id: {bsonType: "string"},
                            name: {bsonType: "string"},
                            quantity: {bsonType: "double", minimum: 0, exclusiveMinimum: true},
                            unit: {bsonType: "string", enum: ["g", "ml"]},
                            ingredient_id: {bsonType: "string"},
                            nutrition: {
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
            }
        }
    }
};
