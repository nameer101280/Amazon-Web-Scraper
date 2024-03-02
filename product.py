class Product:
    def __init__(self, title, price, total_reviews, image_url):
        self.title = title
        self.price = price
        self.total_reviews = total_reviews
        self.image_url = image_url

    def display_product_details(self):
        print(f"Title: {self.title}")
        print(f"Price: {self.price}")
        print(f"Total Reviews: {self.total_reviews}")
        print(f"Image URL: {self.image_url}")

    def to_dict(self):
        return {
            "title": self.title,
            "price": self.price,
            "total_reviews": self.total_reviews,
            "image_url": self.image_url
        }

    @staticmethod
    def from_dict(data):
        return Product(
            title=data.get("title"),
            price=data.get("price"),
            total_reviews=data.get("total_reviews"),
            image_url=data.get("image_url")
        )
