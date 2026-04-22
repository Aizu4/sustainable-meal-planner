var ingredientProperties = {
  bsonType: "object",
  required: [
    "id",
    "name",
    "values"
  ],
  properties: {
    id: {
      bsonType: "string"
    },
    name: {
      bsonType: "string"
    },
    category: {
      bsonType: "string"
    },
    allergens: {
      bsonType: "array",
      items: {
        bsonType: "int"
      },
      uniqueItems: true
    },
    is_vegan: {
      bsonType: "bool"
    },
    is_gluten_free: {
      bsonType: "bool"
    },
    values: {
      bsonType: "object",
      required: [
        "base_quantity",
        "base_unit",
        "nutrition"
      ],
      properties: {
        base_quantity: {
          bsonType: "double",
          minimum: 0,
          exclusiveMinimum: true
        },
        base_unit: {
          bsonType: "string",
          enum: [
            "g",
            "ml"
          ]
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
        }
      }
    }
  }
};

var ingredientSchema = {
  validator: {
    $jsonSchema: ingredientProperties
  }
};
