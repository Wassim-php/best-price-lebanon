import apiClient from "./apiClient";

const ProductService = {
    async compare(query) {
        try {
            const response = await apiClient.post("/comparisons/compare", query);
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.message || error.message || "Error fetching and comparing products";
            throw new Error(errorMessage);
        }
    }
};

export default ProductService;
