from werkzeug.exceptions import InternalServerError


class ApiProblem(InternalServerError):
    """
    Note: Extends InternalServerError instead of HTTPException
    so default status code and description are set as generic error

    from: https://tools.ietf.org/html/rfc7807

    A problem details object can have the following members:

    o  "type" (string) - A URI reference [RFC3986] that identifies the
       problem type. This specification encourages that, when
       dereferenced, it provide human-readable documentation for the
       problem type (e.g., using HTML [W3C.REC-html5-20141028]). When
       this member is not present, its value is assumed to be
       "about:blank".

    o  "title" (string) - A short, human-readable summary of the problem
       type.  It SHOULD NOT change from occurrence to occurrence of the
       problem, except for purposes of localization (e.g., using
       proactive content negotiation; see [RFC7231], Section 3.4).

    o  "status" (number) - The HTTP status code ([RFC7231], Section 6)
       generated by the origin server for this occurrence of the problem.

    o  "detail" (string) - A human-readable explanation specific to this
       occurrence of the problem.

    o  "instance" (string) - A URI reference that identifies the specific
       occurrence of the problem. It may or may not yield further
       information if dereferenced.

    Consumers MUST use the "type" string as the primary identifier for
    the problem type; the "title" string is advisory and included only
    for users who are not aware of the semantics of the URI and do not
    have the ability to discover them (e.g., offline log analysis).
    Consumers SHOULD NOT automatically dereference the type URI.

    The "status" member, if present, is only advisory; it conveys the
    HTTP status code used for the convenience of the consumer.
    Generators MUST use the same status code in the actual HTTP response,
    to assure that generic HTTP software that does not understand this
    format still behaves correctly. See Section 5 for further caveats
    regarding its use.

    Consumers can use the status member to determine what the original
    status code used by the generator was, in cases where it has been
    changed (e.g., by an intermediary or cache), and when message bodies
    persist without HTTP information. Generic HTTP software will still
    use the HTTP status code.

    The "detail" member, if present, ought to focus on helping the client
    correct the problem, rather than giving debugging information.
    """
    headers = {}
    response = None
    type = 'https://httpstatuses.com/{}'
    instance = 'about:blank'
    ct_id = 'problem'

    def __init__(self, description=None, response=None, **kwargs):
        """

        :param description:
        :param response:

        :param data:
        """
        super().__init__(description, response)

        self.type = kwargs.get('type', self.type.format(self.code))
        self.instance = kwargs.get('instance', self.instance)

        h = kwargs.get('headers', {})

        try:
            self.headers.update(**h)
        except AttributeError:
            self.headers = h

    def prepare_response(self):
        """

        """
        return dict(
            type=self.type,
            title=self.name,
            status=self.code,
            instance=self.instance,
            response=self.response,
            detail=self.description
        ), self.code, self.fix_headers()

    def fix_headers(self):
        """

        :return:
        """
        ct = self.headers.get('Content-Type')
        if ct:
            if ApiProblem.ct_id not in ct:
                self.headers.update({
                    'Content-Type': "/{}".format(ApiProblem.ct_id).join(ct.split('/', maxsplit=1))
                })
        else:
            self.headers.update({
                'Content-Type': 'x-application/{}'.format(self.ct_id)
            })

        return self.headers
