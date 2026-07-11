import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { importsApi } from '../../api/httpClient'
import { ImportCsvModal } from './ImportCsvModal'

vi.mock('../../api/httpClient', () => ({
  importsApi: {
    previewPeople: vi.fn(),
    commitPeople: vi.fn(),
  },
}))

describe('ImportCsvModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('commits large imports in batches of 100', async () => {
    const rows = Array.from({ length: 101 }, (_, index) => ({
      row_number: index + 2,
      status: 'valid',
      name: `Person ${index}`,
      linkedin_url: `https://linkedin.com/in/person-${index}/`,
      errors: [],
    }))
    vi.mocked(importsApi.previewPeople).mockResolvedValue({
      import_batch_id: 'batch-1',
      summary: { total_rows: 101, valid_rows: 101, duplicate_rows: 0, invalid_rows: 0 },
      rows,
    })
    vi.mocked(importsApi.commitPeople).mockResolvedValue({
      summary: { created_count: 1, skipped_duplicates: 0, failed_count: 0 },
    })

    render(
      <ImportCsvModal
        isOpen
        workspaceId="workspace-1"
        onClose={vi.fn()}
        onImported={vi.fn()}
      />,
    )

    const file = new File(['name,linkedin_url'], 'people.csv', { type: 'text/csv' })
    fireEvent.change(screen.getByLabelText('CSV File'), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview Import' }))
    await screen.findByRole('button', { name: 'Confirm Import (101)' })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Import (101)' }))

    await waitFor(() => expect(importsApi.commitPeople).toHaveBeenCalledTimes(2))
    expect(vi.mocked(importsApi.commitPeople).mock.calls[0][0]).toMatchObject({
      chunk_index: 0,
      total_chunks: 2,
    })
    expect(vi.mocked(importsApi.commitPeople).mock.calls[0][0].rows).toHaveLength(100)
    expect(vi.mocked(importsApi.commitPeople).mock.calls[1][0]).toMatchObject({
      chunk_index: 1,
      total_chunks: 2,
    })
    expect(vi.mocked(importsApi.commitPeople).mock.calls[1][0].rows).toHaveLength(1)
  })
})
