import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { useAuth } from '../auth'

type Step = { title: string; body: ReactNode }

const STUDENT_STEPS: Step[] = [
  {
    title: 'File a lost report',
    body: (
      <>
        Go to <Link to="/reports/new">My lost reports → File a lost report</Link>. Pick a category, give it a clear
        title like "Black Samsung phone", and say when and where you lost it. Under identifying details, write
        something only the owner would know: a sticker, a scratch, what's inside. Only you and the security office see
        those details.
      </>
    ),
  },
  {
    title: 'Check for matches',
    body: (
      <>
        Open your report. Found items that match it by 60% or more are listed there, with where each was found and who
        to meet. If nothing matches yet, that's fine: we'll send you a notification as soon as a matching item is
        added.
      </>
    ),
  },
  {
    title: 'Go to the security office',
    body: (
      <>
        If one of the matches looks like yours, go to the security office and meet the person listed. They'll check
        your identifying details against the item. If it's yours, they approve you in the app.
      </>
    ),
  },
  {
    title: 'Collect it with your pickup code',
    body: (
      <>
        After approval, a 6-digit code appears on <Link to="/claims">Pickup codes</Link>. Tell it to the guard and take
        your item. Your lost report then shows <strong>Closed</strong>.
      </>
    ),
  },
]

const ADMIN_STEPS: Step[] = [
  {
    title: 'Add every found item',
    body: (
      <>
        Use <Link to="/admin/items/new">Add found item</Link>. Category, title, date and general area help students
        find it. The exact location, description and photo are private: students never see them, so you can use them
        to check who the real owner is.
      </>
    ),
  },
  {
    title: 'Students are told automatically',
    body: (
      <>
        Anyone whose lost report matches the item by 60% or more gets a notification telling them where to come and
        who to meet.
      </>
    ),
  },
  {
    title: 'Check the person, then approve',
    body: (
      <>
        When someone comes to the office, open the item from the <Link to="/admin">Security desk</Link>. Under{' '}
        <strong>Who may own this</strong>, compare their identifying details with the item and click{' '}
        <strong>Approve</strong>. If they never filed a report, use <strong>Approve someone else</strong> with their
        email. Approved the wrong person? Click <strong>Cancel approval</strong>.
      </>
    ),
  },
  {
    title: 'Hand over with the pickup code',
    body: (
      <>
        The student gets a 6-digit code in the app. Ask them for it and enter it under <strong>Hand over</strong>. The
        item is marked returned and logged on <Link to="/admin/handovers">Handovers</Link>.
      </>
    ),
  },
]

export default function GuidePage() {
  const { user } = useAuth()

  const admin = user?.is_admin
  const steps = admin ? ADMIN_STEPS : STUDENT_STEPS

  return (
    <>
      <h1>How IITGN Lost &amp; Found works</h1>

      <h2>{admin ? 'For the security office' : 'If you lost something'}</h2>
      <ol className="steps">
        {steps.map((step, i) => (
          <li key={step.title} className="card">
            <span className="step-number" aria-hidden="true">
              {i + 1}
            </span>
            <div>
              <strong>{step.title}</strong>
              <p>{step.body}</p>
            </div>
          </li>
        ))}
      </ol>

      <h2>Good to know</h2>
      <ul className="card tips">
        {admin ? (
          <>
            <li>
              Other guards can be given access on the <Link to="/admin/admins">Admins</Link> page.
            </li>
            <li>A pickup code works only once, so an item can't be collected twice.</li>
            <li>Admins can't file lost reports. Use a personal account for your own lost items.</li>
          </>
        ) : (
          <>
            <li>
              Watch <Link to="/notifications">Notifications</Link>: that's where matches and approvals show up.
            </li>
            <li>The more specific your title and place, the better the matches.</li>
            <li>Never share your pickup code with anyone except the guard handing over your item.</li>
          </>
        )}
      </ul>

      <p>
        <Link className="button" to={admin ? '/admin' : '/reports/new'}>
          {admin ? 'Go to the security desk' : 'File a lost report'}
        </Link>
      </p>
    </>
  )
}
