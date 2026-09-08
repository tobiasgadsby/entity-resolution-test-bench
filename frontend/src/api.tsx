
export type Dataset = {
    dataset_id: string,
    dataset_name: string,
    base_data_last_updated: string,
    base_data_count: number,
    skewed_data_last_updated: string,
    skewed_data_count: number
}

export type RunHistory = {
    run_id: string,
    dataset_id: string,
    timestamp: string,
    technique: string,
    total_records: number,
    true_positives: number,
    false_positives: number,
    true_negatives: number,
    false_negatives: number
}

export type SkewedTechnique = {
    id: string,
    name: string
}

export type BaseData = {
    id: string,
    dataset_id: string,
    first_name: string,
    last_name: string,
    full_name: string[]
}

export type SkewedData = {
    id: string,
    dataset_id: string,
    base_data_id: string,
    first_name: string,
    last_name: string
}

export type SemanticTechniqueRequest = {
    dataset_id: string,
    k_nearest_neighbours: number,
    num_of_candidates: number,
}

export type TechniqueRequest = {
    dataset_id: string
}

export type LevenshteinRequest = {
    dataset_id: string;
    levenshteinFuzziness: number;
    levenshteinMinShouldMatch: number;
}