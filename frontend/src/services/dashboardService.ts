import type { ApiResult, DashboardStats, User } from "../types";
import { getMockDashboardStats } from "../mock/mockData";
import { delay } from "./utils";

export async function fetchDashboardStats(user?: User | null): Promise<ApiResult<DashboardStats>> {
  await delay(400);
  return { ok: true, data: getMockDashboardStats(user) };
}

