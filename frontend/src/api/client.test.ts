import axios, { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './client'
import { useAuthStore } from '../store/auth'

const originalAdapter = api.defaults.adapter

describe('API token refresh', () => {
  beforeEach(() => {
    useAuthStore.setState({
      accessToken: 'expired-token',
      user: null,
      bootstrapped: true,
    })
  })

  afterEach(() => {
    api.defaults.adapter = originalAdapter
    useAuthStore.getState().clearAuth()
    vi.restoreAllMocks()
  })

  it('refreshes once and retries a request after a 401', async () => {
    const refreshResponse: AxiosResponse<{ access_token: string }> = {
      data: { access_token: 'fresh-token' },
      status: 200,
      statusText: 'OK',
      headers: new AxiosHeaders(),
      config: { headers: new AxiosHeaders() },
    }
    const refresh = vi.spyOn(axios, 'post').mockResolvedValue(refreshResponse)
    api.defaults.adapter = async (config) => {
      if (config.headers.Authorization !== 'Bearer fresh-token') {
        throw new AxiosError(
          'Unauthorized',
          'ERR_BAD_REQUEST',
          config,
          undefined,
          {
            data: {},
            status: 401,
            statusText: 'Unauthorized',
            headers: new AxiosHeaders(),
            config,
          },
        )
      }
      return {
        data: { ok: true },
        status: 200,
        statusText: 'OK',
        headers: new AxiosHeaders(),
        config,
      }
    }

    const response = await api.get('/protected')

    expect(response.data).toEqual({ ok: true })
    expect(refresh).toHaveBeenCalledOnce()
    expect(useAuthStore.getState().accessToken).toBe('fresh-token')
  })
})
