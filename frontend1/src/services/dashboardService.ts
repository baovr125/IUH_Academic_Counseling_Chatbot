import type { ApiResult, DashboardStats } from "../types";
import { MOCK_DASHBOARD_STATS } from "../mock/mockData";
import { delay } from "./utils";

export async function fetchDashboardStats(): Promise<ApiResult<DashboardStats>> {
  await delay(900);
  return { ok: true, data: MOCK_DASHBOARD_STATS };
}
