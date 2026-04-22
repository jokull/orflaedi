import raw from "./models.json";

export type Retailer = {
  id: number;
  name: string;
  slug: string;
  website_url: string | null;
};

export type Tag = { name: string; label: string };
export type Classification = { short: string; long: string };
export type PriceRange = [string, number | null, number | null];

export type Model = {
  id: number;
  name: string;
  make: string | null;
  classification: string | null;
  price: number | null;
  retailer_id: number;
  tags: string[];
  scrape_url: string;
  images: { "1x": string; "2x"?: string; "3x"?: string };
};

export type DataFile = {
  generated_at: string;
  retailers: Retailer[];
  models: Model[];
  classifications: Classification[];
  tags: Tag[];
  price_ranges: PriceRange[];
};

export const data = raw as DataFile;
export const modelsById = new Map(data.models.map((m) => [m.id, m]));
export const retailerById = new Map(data.retailers.map((r) => [r.id, r]));
