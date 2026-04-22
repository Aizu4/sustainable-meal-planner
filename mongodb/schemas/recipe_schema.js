// ingredientProperties is defined in ingredient_schema.js, which is loaded first in mongo-init.js

var recipeSchema = {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "id",
        "name",
        "ingredients"
      ],
      properties: {
        id: {
          bsonType: "string"
        },
        name: {
          bsonType: "string"
        },
        servings: {
          bsonType: "int",
          minimum: 1
        },
        image_url: {
          bsonType: "string"
        },
        source_url: {
          bsonType: "string"
        },
        cooking_time: {
          bsonType: "int",
          minimum: 0
        },
        is_vegan: {
          bsonType: "bool"
        },
        is_gluten_free: {
          bsonType: "bool"
        },
        allergens: {
          bsonType: "array",
          items: {
            bsonType: "int"
          },
          uniqueItems: true
        },
        carbon_footprint: {
          bsonType: "double",
          minimum: 0
        },
        nutrition: {
          bsonType: "object",
          required: [
            "kcal",
            "macro"
          ],
          properties: {
            kcal: {
              bsonType: "double",
              minimum: 0
            },
            macro: {
              bsonType: "object",
              required: [
                "carbs",
                "protein",
                "fat"
              ],
              properties: {
                carbs: {
                  bsonType: "double",
                  minimum: 0
                },
                protein: {
                  bsonType: "double",
                  minimum: 0
                },
                fat: {
                  bsonType: "double",
                  minimum: 0
                },
                fiber: {
                  bsonType: "double",
                  minimum: 0
                },
                sugar: {
                  bsonType: "double",
                  minimum: 0
                }
              }
            }
          }
        },
        ingredients: {
          bsonType: "array",
          minItems: 1,
          items: {
            ...ingredientProperties,
            required: [
              ...ingredientProperties.required,
              "quantity"
            ],
            properties: {
              ...ingredientProperties.properties,
              quantity: {
                bsonType: "double",
                minimum: 0,
                exclusiveMinimum: true
              }
            }
          }
        }
      }
    }
  }
};
