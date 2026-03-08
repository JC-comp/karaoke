import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import { useJob } from '@/hooks/job/useJob';
import { getStatusIcon } from '@/utils/icon';

export default function ProgressTab() {
  const { isLoading, jobs } = useJob('*', false);
  
  return <div>
    <table className="table table-striped table-hover text-center" style={{ tableLayout: 'fixed' }}>
      <tbody>
        {
          Object.values(jobs).map((job) => (
            <tr key={job.jid}>
              <td>
                <div className='d-flex align-items-center'>
                  <span title={job.status || 'none'} className='p-2'>
                    {getStatusIcon(job.status)}
                  </span>
                  <Link className='text-decoration-none overflow-hidden' href={`/job?jobId=${btoa(job.jid)}`}>
                    <div className='text-truncate'>
                      {job.artifact_tags.metadata ? job.artifact_tags.metadata.value?.title : job.jid}
                    </div>
                  </Link>
                </div>
              </td>
            </tr>
          ))
        }
      </tbody>
    </table>
    {
      isLoading ? (
        <div className="d-flex justify-content-center align-items-center my-2">
          <FontAwesomeIcon icon={faSpinner} spin size="2x" />
        </div>
      ) : Object.keys(jobs).length === 0 && (
        <div className="alert alert-info w-100" role="alert">
          No jobs found.
        </div>
      )
    }
  </div>
}
