import apiClient from "./apiClient";

export const normalizeSearchHistory = (data) => {
    const rawItems = Array.isArray(data)
        ? data
        : Array.isArray(data?.history)
            ? data.history
            : Array.isArray(data?.results)
                ? data.results
                : Array.isArray(data?.searches)
                    ? data.searches
                    : [];

    return rawItems
        .map((item) => {
            if (typeof item === "string") {
                return {
                    id: null,
                    query: item,
                    createdAt: null,
                    minPrice: null,
                    resultCount: null,
                    sitesChecked: null,
                    sitesSucceeded: null,
                    topResult: null,
                };
            }

            if (!item || typeof item !== "object") {
                return null;
            }

            const query =
                item.query ||
                item.search_query ||
                item.searchTerm ||
                item.term ||
                item.product_name ||
                item.title ||
                "";

            if (!query) {
                return null;
            }

            return {
                id: item.id ?? null,
                query,
                location: item.location ?? null,
                createdAt: item.created_at ?? item.createdAt ?? null,
                minPrice: item.min_price ?? item.minPrice ?? null,
                resultCount: item.result_count ?? item.resultCount ?? null,
                sitesChecked: item.sites_checked ?? item.sitesChecked ?? null,
                sitesSucceeded: item.sites_succeeded ?? item.sitesSucceeded ?? null,
                topResult: item.top_result ?? item.topResult ?? null,
                username: item.username ?? null,
            };
        })
        .filter(Boolean);
};

export const mapSearchDetailsToComparisonResults = (details) => {
    const rawResults = Array.isArray(details?.results) ? details.results : [];

    return {
        results: rawResults.map((result) => ({
            source: result.source,
            score: result.score != null ? Number(result.score) : null,
            store_rating: result.store_rating != null ? Number(result.store_rating) : null,
            delivery_days: result.delivery_days,
            product: {
                title: result.product_title,
                url: result.product_url,
                image_url: result.image_url,
                in_stock: result.in_stock,
            },
            pricing: {
                item_price: result.item_price != null ? Number(result.item_price) : null,
                shipping_fee: result.shipping_fee != null ? Number(result.shipping_fee) : 0,
                total_price: result.total_price != null ? Number(result.total_price) : null,
                delivery_time: result.delivery_time,
            },
            score_breakdown: {
                price_score: result.score_breakdown?.price_score ?? null,
                delivery_score: result.score_breakdown?.delivery_score ?? null,
                trust_score: result.score_breakdown?.trust_score ?? null,
            },
        })),
        metadata: {
            min_price: details?.min_price ?? null,
            sites_checked: details?.sites_checked ?? null,
            sites_succeeded: details?.sites_succeeded ?? null,
            search_id: details?.id ?? null,
        },
    };
};

const HistoryService = {
    async getUserSearchHistory() {
        try {
            const response = await apiClient.get("/comparisons/history");
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.message || error.message || "Failed fetching user history.";
            throw new Error(errorMessage);
        }
    },

    async getSearchDetails(id) {
        try {
            const response = await apiClient.get(`/comparisons/${id}`);
            return response.data;

        } catch (error) {
            const errorMessage = error.response?.data?.message || error.message || "Failed fetching user history.";
            throw new Error(errorMessage);
        }
    },

    async clearHistory(){
        try{
            const response = await apiClient.delete("/comparisons/history/clear");
            return response.data;
        }catch(error){
            const errorMessage = error.response?.data?.message || error.message || "Failed fetching user history.";
            throw new Error(errorMessage);
        }
    }
};

export default HistoryService;